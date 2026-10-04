from tools.tools import web_search

#results = scrape_url(" https://www.ibm.com/think/topics/artificial-intelligence")
#print(results)

r = web_search.invoke("what is the latest research on using AI for climate change mitigation?")
print(r)

