import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class WebCrawler:
    """
    A lightweight, robust web crawler that retrieves SUT pages, extracts the link structures,
    and performs a static DOM audit of interactive components (roles, names, options, and selectors).
    Allows modular fallback to Playwright if needed in other environments.
    """
    
    def __init__(self, base_url: str, max_depth: int = 2, max_pages: int = 5):
        self.base_url = base_url.rstrip("/")
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls = set()
        self.domain = urlparse(base_url).netloc
        self.pages_data = {}

    def is_internal_url(self, url: str) -> bool:
        parsed_url = urlparse(url)
        # Handle relative links or same domain
        return not parsed_url.netloc or parsed_url.netloc == self.domain

    def clean_url(self, url: str) -> str:
        # Strip query params and hashes for crawler paths
        parsed = urlparse(url)
        return parsed._replace(query="", fragment="").geturl()

    async def crawl(self) -> Dict[str, Any]:
        """
        Crawls the SUT starting from base_url, following internal links up to max_depth.
        Returns a dictionary of path -> page_details.
        """
        async with aiohttp.ClientSession() as session:
            await self._crawl_page(session, self.base_url, depth=1)
        return self.pages_data

    async def _crawl_page(self, session: aiohttp.ClientSession, url: str, depth: int):
        if len(self.pages_data) >= self.max_pages:
            return
            
        clean_url = self.clean_url(url)
        if clean_url in self.visited_urls or depth > self.max_depth:
            return
        
        self.visited_urls.add(clean_url)
        logger.info(f"Crawling URL: {clean_url}")
        
        try:
            async with session.get(clean_url, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {clean_url}: status {response.status}")
                    return
                
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return
                
                html = await response.text()
                parsed_data = self.parse_html(html, clean_url)
                
                # Save path relative to base_url or absolute if needed
                parsed_url = urlparse(clean_url)
                path = parsed_url.path if parsed_url.path else "/"
                self.pages_data[path] = parsed_data
                
                # Discover links
                if depth < self.max_depth:
                    tasks = []
                    for link in parsed_data["discovered_links"]:
                        tasks.append(self._crawl_page(session, link, depth + 1))
                    if tasks:
                        await asyncio.gather(*tasks)
                        
        except Exception as e:
            logger.error(f"Error crawling {clean_url}: {e}")

    def parse_html(self, html: str, current_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        
        title = soup.title.string.strip() if soup.title else "Untitled Page"
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "").strip()
            
        discovered_links = []
        interactive_elements = []
        
        # 1. Discover links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            abs_url = urljoin(current_url, href)
            if self.is_internal_url(abs_url):
                clean_abs = self.clean_url(abs_url)
                if clean_abs not in discovered_links and clean_abs != self.base_url + "/api":
                    discovered_links.append(clean_abs)
                    
        # 2. Extract buttons, inputs, selects
        # Find inputs
        for input_tag in soup.find_all("input"):
            # Skip hidden inputs
            if input_tag.get("type") == "hidden":
                continue
            
            elem_id = input_tag.get("id", "")
            elem_name = input_tag.get("name", "")
            elem_type = input_tag.get("type", "text")
            
            # Map type to semantic ARIA role
            role = elem_type
            if elem_type in ["text", "email", "password"]:
                role = "textbox"
            elif elem_type == "number":
                role = "spinbutton"
            elif elem_type in ["radio", "checkbox"]:
                role = elem_type
            
            # Determine visual name or label
            label_text = self._find_label_for_input(soup, input_tag)
            
            # Formulate selector
            if elem_id:
                selector = f"input#{elem_id}"
            elif elem_name:
                if elem_type in ["radio", "checkbox"]:
                    val = input_tag.get("value", "")
                    selector = f"input[name='{elem_name}'][value='{val}']"
                else:
                    selector = f"input[name='{elem_name}']"
            else:
                selector = "input"
                
            # Options (for radios/checkboxes)
            options = []
            if elem_type == "radio" and elem_name:
                options = [input_tag.get("value", "")]
                
            interactive_elements.append({
                "type": "input",
                "tag": "input",
                "role": role,
                "name": label_text or elem_name or elem_id or elem_type,
                "selector": selector,
                "id": elem_id,
                "html_name": elem_name,
                "value": input_tag.get("value", ""),
                "options": options
            })

        # Find select elements
        for select_tag in soup.find_all("select"):
            elem_id = select_tag.get("id", "")
            elem_name = select_tag.get("name", "")
            
            label_text = self._find_label_for_input(soup, select_tag)
            
            selector = f"select#{elem_id}" if elem_id else (f"select[name='{elem_name}']" if elem_name else "select")
            
            # Parse select options
            options = [opt.get("value") or opt.text.strip() for opt in select_tag.find_all("option")]
            
            interactive_elements.append({
                "type": "select",
                "tag": "select",
                "role": "combobox",
                "name": label_text or elem_name or elem_id or "select",
                "selector": selector,
                "id": elem_id,
                "html_name": elem_name,
                "options": options
            })
            
        # Find buttons
        for btn_tag in soup.find_all(["button", "a"]):
            # For `a` tags, only include if they have role="button", class or text indicating it's a CTA button
            is_button = btn_tag.name == "button"
            if not is_button:
                classes = " ".join(btn_tag.get("class", []))
                role = btn_tag.get("role", "")
                if "btn" in classes or "button" in classes or role == "button" or btn_tag.text.strip().endswith("→"):
                    is_button = True
            
            if not is_button:
                continue
                
            elem_id = btn_tag.get("id", "")
            name_text = btn_tag.text.strip() or btn_tag.get("aria-label", "").strip() or btn_tag.get("title", "").strip()
            
            # clean double whitespaces
            name_text = " ".join(name_text.split())
            
            # Skip empty buttons
            if not name_text:
                continue
                
            if btn_tag.name == "button":
                selector = f"button#{elem_id}" if elem_id else f"button:has-text('{name_text}')"
            else:
                href = btn_tag.get("href", "")
                selector = f"a[href='{href}']" if href else f"a:has-text('{name_text}')"
                
            interactive_elements.append({
                "type": "button",
                "tag": btn_tag.name,
                "role": "button",
                "name": name_text,
                "selector": selector,
                "id": elem_id
            })
            
        # De-duplicate radio buttons with the same name into group details
        grouped_elements = self._coalesce_elements(interactive_elements)
            
        return {
            "title": title,
            "description": description,
            "url": current_url,
            "interactive_elements": grouped_elements,
            "discovered_links": discovered_links
        }
        
    def _find_label_for_input(self, soup: BeautifulSoup, element) -> str:
        elem_id = element.get("id", "")
        # Try finding <label for="id">
        if elem_id:
            label = soup.find("label", attrs={"for": elem_id})
            if label:
                return label.text.strip()
                
        # Try finding parent <label>
        parent = element.parent
        while parent:
            if parent.name == "label":
                # Extract text without input text
                label_text = "".join([t for t in parent.contents if isinstance(t, str) or t.name not in ["input", "select"]])
                return label_text.strip()
            parent = parent.parent
            
        # Try finding preceding text or custom styles
        # NextJS custom structures: check parent container labels
        container = element.parent
        for _ in range(3): # check up to 3 parent levels
            if container:
                label_span = container.find(["span", "label", "p"], class_=lambda c: c and ("label" in c or "title" in c or "font-mono" in c))
                if label_span and label_span.text.strip():
                    return label_span.text.strip()
                container = container.parent
                
        return ""

    def _coalesce_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups separate radio inputs of the same group into a single structured list of options.
        """
        coalesced = []
        radios = {}
        
        for elem in elements:
            if elem.get("role") == "radio" and elem.get("html_name"):
                name = elem["html_name"]
                if name not in radios:
                    radios[name] = {
                        "type": "radio_group",
                        "tag": "input",
                        "role": "radio_group",
                        "name": elem["name"] or name, # Use first label or name
                        "selector": f"input[name='{name}']",
                        "id": elem["id"],
                        "html_name": name,
                        "options": []
                    }
                # Check option text label
                opt_val = elem["value"]
                # Look for label text again if it's customized per radio
                opt_label = elem["name"] or opt_val
                radios[name]["options"].append({"label": opt_label, "value": opt_val})
            else:
                coalesced.append(elem)
                
        # Add back grouped radios
        for radio_group in radios.values():
            # Refine the radio group label based on parent span (like "Sex" or "Smoking")
            # If the label is same as one of the options (e.g. Male), we might need to find a broader label
            coalesced.append(radio_group)
            
        return coalesced

# Local Testing Block
if __name__ == "__main__":
    import sys
    # Avoid Windows console encoding issues with non-ASCII characters
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO)
    crawler = WebCrawler("https://healthspan.assurecraft.org")
    results = asyncio.run(crawler.crawl())
    import pprint
    pprint.pprint(results)
