import webbrowser
import time

# URLs to open


url = "http://localhost:3000"

routes = ["/", 
          "/processes"]

# Open URLs in Chrome
for route in routes:
    webbrowser.open(f"{url}{route}", new=2)  # new=2 opens in a new tab
    time.sleep(1)  # Small delay to ensure they open smoothly
