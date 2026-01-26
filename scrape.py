import os
import json
from requests import post
from bs4 import BeautifulSoup as Soup

apikey = os.environ['ZYTE_KEY']

def get_html(url):
    r = post(
        "https://api.zyte.com/v1/extract",
        auth=(apikey, ""),
        json={"url": url, "browserHtml": True, "actions": [{"action": "scrollBottom"}]},
        timeout=60
    )
    return r.json()["browserHtml"]

def get_all_signs(sector, market):
    url = f'https://www.set.or.th/th/market/index/{market}/{sector}'
    soup = Soup(get_html(url), 'html.parser')
    res = []
    for a in soup.select('a.text-symbol'):
        sym = a['data-symbol']
        signs = [item.text.strip() for item in a.select('div.item-sign')]
        res.append({"symbol": sym, "signs": signs})
    return res

if __name__ == "__main__":
    markets = ['set', 'mai']
    sectors = "agro consump fincial indus propcon resourc service tech".split()
    all_signs = []
    
    for market in markets:
        for sect in sectors:
            sect_signs = get_all_signs(sect, market)
            all_signs.extend(sect_signs)
            print(f"{market}/{sect}: {len(sect_signs)}")
    
    print(f"Total: {len(all_signs)}")
    
    # Save to pretty JSON
    with open('set_signs.json', 'w', encoding='utf-8') as f:
        f.write('[\n')
        for i, item in enumerate(all_signs):
            comma = ',' if i < len(all_signs) - 1 else ''
            f.write(f'{json.dumps(item, ensure_ascii=False)}{comma}\n')
        f.write(']\n')
    
    print("Saved to set_signs.json")
