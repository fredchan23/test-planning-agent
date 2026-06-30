import pytest
from test_planner_agent.crawler import WebCrawler

def test_crawler_parsing():
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>
                <a href="/explore">Explore</a>
                <a href="https://external.com">External</a>
            </nav>
            <main>
                <label for="age_input">Age:</label>
                <input id="age_input" type="number" name="age" value="30">
                
                <label>Sex:
                    <input type="radio" name="sex" value="male" checked> Male
                    <input type="radio" name="sex" value="female"> Female
                </label>
                
                <select id="risk_select" name="risk">
                    <option value="low">Low</option>
                    <option value="high">High</option>
                </select>
                
                <button id="submit_btn">Calculate</button>
            </main>
        </body>
    </html>
    """
    
    crawler = WebCrawler("https://healthspan.assurecraft.org")
    parsed = crawler.parse_html(html_content, "https://healthspan.assurecraft.org/")
    
    assert parsed["title"] == "Test Page"
    
    # Check discovered links
    assert len(parsed["discovered_links"]) == 1
    assert parsed["discovered_links"][0] == "https://healthspan.assurecraft.org/explore"
    
    # Check elements
    elems = parsed["interactive_elements"]
    
    # We should have:
    # 1. age input (textbox/spinbutton)
    # 2. sex radio group
    # 3. risk select (combobox)
    # 4. calculate button
    elem_types = [e["type"] for e in elems]
    assert "input" in elem_types # age input
    assert "radio_group" in elem_types # sex radio group
    assert "select" in elem_types # risk select
    assert "button" in elem_types # calculate button
    
    # Verify age input selector
    age_elem = next(e for e in elems if e["id"] == "age_input")
    assert age_elem["selector"] == "input#age_input"
    assert age_elem["role"] == "spinbutton"
    
    # Verify sex radio group
    sex_elem = next(e for e in elems if e["role"] == "radio_group")
    assert len(sex_elem["options"]) == 2
    assert sex_elem["options"][0]["value"] == "male"
    assert sex_elem["options"][1]["value"] == "female"
