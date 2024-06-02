import os
import re
import praw
import requests

reddit = praw.Reddit('launchBot')

subreddit = reddit.subreddit("pythonforengineers")

commentPattern = re.compile("(when is|when's|when does)\s+(rocketlab|rocketlab's)\s+launch", re.IGNORECASE)
def get_next_launch():
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
    params = {
        "hide_recent_previous": "true",
        "include_suborbital": "true",
        "limit":1,
        "lsp__id":"147"
    }
    response = requests.get(url, params)
    print("Request made to: ", response.url)

    if response.status_code==200:
        launches = response.json().get("results",[])
        if launches:
            print("Found a launch")
            
            launch = launches[0]
           
            launch_window_start = launch.get("window_start")
            rocket_name = launch.get("rocket", {}).get("configuration", {}).get("name")
            mission_name = launch.get("mission", {}).get("name")
            mission_description = launch.get("mission", {}).get("description")
            agencies = launch.get("mission").get("agencies", [])
            print("Agencies data:", agencies)  # Debugging: Print the agencies data
            pad_name = launch.get("pad", {}).get("name")
            pad_location_name = launch.get("pad", {}).get("location", {}).get("name")
            agency_launch_attempt_count_year = launch.get("agency_launch_attempt_count_year",{})
            agency_launch_attempt_count = launch.get("agency_launch_attempt_count",{})
            agencies_info = ""
            for agency in agencies:
                    print("Found agency")
                    agency_name = agency.get("name")
                    agency_abbrev = agency.get("abbrev")
                    if(agency_abbrev):
                        agencies_info += agency_name + " (" + agency_abbrev + "),"
                    else:
                        agencies_info += agency_name+","
            agencies_info = agencies_info.rstrip(", ")
                    
            launch_info = (
                f"Rocket Lab is launching {rocket_name} next, on {launch_window_start} from {pad_name} ({pad_location_name}).    "
                f"They are launching {mission_name} {'for' if len(agencies)==1 else 'a rideshare mission for '} {agencies_info}.    "
                f"This is launch #{agency_launch_attempt_count_year} this year, and launch #{agency_launch_attempt_count} overall.    "
                f"The mission is stated as follows: {mission_description}"
            )
            return launch_info
        return "Could not retrieve launch information"


if not os.path.isfile("comments_replied_to.txt"):
    comments_replied_to = []
else:
    with open("comments_replied_to.txt", "r") as f:
       comments_replied_to = f.read()
       comments_replied_to = comments_replied_to.split("\n")
       comments_replied_to = list(filter(None, comments_replied_to))
       

launchInfo = get_next_launch()
print(launchInfo)
try:
    for comment in subreddit.stream.comments():
        print("Found new comment")
        if commentPattern.search(comment.body):
            print("Found a comment asking about Rocket Lab's next launch")
            #below commented out for testing
            # if comment.author.name != reddit.user.me().name:
            if(comment.id not in comments_replied_to):
                try:
                    #comment.reply(launchInfo)
                    comments_replied_to.append(comment.id)
                    print("Replied to:", comment.id)
                except Exception as e:
                    print("Error replying to comment:", e)
except KeyboardInterrupt:
    print("Stopped by user")


with open("comments_replied_to.txt", "w") as f:
    for comment_id in comments_replied_to:
        f.write(comment_id + "\n")
            
    
            
                
                    
                    
                        