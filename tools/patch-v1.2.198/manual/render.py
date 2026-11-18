# Render ulang PDF panduan dari manual.html (butuh: pip install playwright && playwright install chromium)
import asyncio, os
D=os.path.dirname(os.path.abspath(__file__))
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page()
        await pg.goto('file://'+D+'/manual.html'); await pg.wait_for_timeout(800)
        await pg.pdf(path=D+'/pasang-dashboard-di-hp.pdf', format='A4', print_background=True, prefer_css_page_size=True)
        await b.close()
asyncio.run(main())
