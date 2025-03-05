from bs4 import BeautifulSoup


def get_category_and_level(html_path):
    with open(html_path, "r", encoding="utf-8") as html_file:
        html_content = html_file.read()

    soup = BeautifulSoup(html_content, "lxml")
    div = soup.find("div", class_="topic-level-info row")
    try:
        topic = div.a.text.strip()
    except AttributeError as e:
        topic = "Unclassified"
    level_text = div.find("span", class_="level-text").text.strip()
    level = level_text.replace("Level", "").strip()
    if len(level) == 0:
        level = "Pending"
    topic = topic.title().replace(" ", "")
    level = level.title().replace(" ", "")
    return topic, level
