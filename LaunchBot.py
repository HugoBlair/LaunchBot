from datetime import datetime
import os
import re
import praw
import pytz
import requests

#Accessing the reddit API details from my praw.ini file (which is in the same directory as the script)
#This information is kept private and not included in the repository
reddit = praw.Reddit('launchBot')

#Choosing the subreddits to search for comments in
subreddit = reddit.subreddit("pythonforengineers+test")

#Regex patterns to search for comments with
commentPattern = re.compile(r"when(\sis\s|\sdoes\s|\'s\s|\sare\s|\swill\s)(\S*\s){0,4}launch(?!\scomplex\s\d)",re.IGNORECASE)
rocketPattern = re.compile(r"Electron|Haste|Neutron",re.IGNORECASE)
locationNZPattern = re.compile(r"NZ|New Zealand|Mahia|Launch Complex 1|LC1",re.IGNORECASE)
locationUSPattern = re.compile(r"US|United States|Virginia|USA|Wallops|Launch Complex 2|LC2|MARS",re.IGNORECASE)

#Function to get the next launch from the API
def get_next_launch(rocket = None, location = None):
    try:
        url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
        params = {
            "hide_recent_previous": "true",
            "include_suborbital": "true",
            "limit":1,
            #LSP = Launch Service Provider
            "lsp__id":"147",
            "rocket__configuration__name": rocket,
            "location__ids": location
        }
        response = requests.get(url, params)
        print("Request made to: ", response.url)
        launchInfo = extract_launch_info(response)
        
        #Handling cases where there are no launches scheduled with different query types
        if launchInfo == None:
            if(rocket and not location):
                launchInfo = f"Rocketlab doesn't have any official launches scheduled for {rocket} at the moment  \n"
            elif(location and not rocket):
                launchInfo = f"Rocketlab doesn't have any official launches scheduled at {location} at the moment  \n"
            elif(rocket and location):
                launchInfo = f"Rocketlab doesn't have any official launches scheduled for {rocket} at {location} at the moment  \n"
            else:
                launchInfo = f"Rocketlab doesn't have any official launches scheduled at the moment.  \n"
        return launchInfo
            
        
    except Exception as e:
        exit_handler()
        print("Error retrieving launch information:", e)

#Function to extract the launch information from the API response
def extract_launch_info(response):
    if response.status_code==200:
            launches = response.json().get("results",[])
            if launches:
                
                
                launch = launches[0]
            
                launch_window_start = launch.get("window_start")
                rocket_name = launch.get("rocket", {}).get("configuration", {}).get("name")
                mission_name = launch.get("mission", {}).get("name")
                mission_description = launch.get("mission", {}).get("description")
                agencies = launch.get("mission").get("agencies", [])
                pad_name = launch.get("pad", {}).get("name")
                pad_location_name = launch.get("pad", {}).get("location", {}).get("name")
                agency_launch_attempt_count_year = launch.get("agency_launch_attempt_count_year",{})
                agency_launch_attempt_count = launch.get("agency_launch_attempt_count",{})
                agencies_info = ""
                #Handling the case where there is multiple agencies involved in the mission
                for agency in agencies:
                        agency_name = agency.get("name")
                        agency_abbrev = agency.get("abbrev")
                        if(agency_abbrev):
                            agencies_info += agency_name + " (" + agency_abbrev + "),"
                        else:
                            agencies_info += agency_name+","
                agencies_info = agencies_info.rstrip(", ")
                        
                launch_info = (
                    f"Rocket Lab is launching {rocket_name} next from {pad_name} ({pad_location_name}).  \n\n"
                    f"{convert_time(launch_window_start)}"
                    #If multiple agencies are involved in the mission, it is known as a "Rideshare" mission
                    f"They are launching {mission_name} {'for' if len(agencies)==1 else 'a rideshare mission for '} {agencies_info}.  \n\n"
                    f"The mission is stated as follows: {mission_description}  \n\n"
                    f"This is launch #{agency_launch_attempt_count_year} this year, and launch #{agency_launch_attempt_count} overall.  \n\n"
                    
                    
                )
                print(launch_info)
                return launch_info
            print("Failed to find a launch. Returning None")
            return None

def convert_time(input_time):
    input_time = input_time[:-1]
    
    # Parse the ISO 8601 time string into a datetime object
    dt = datetime.fromisoformat(input_time)
    dt = pytz.utc.localize(dt)
    # Define the UTC and New Zealand time zones
    utc_tz = pytz.timezone('UTC')
    nz_tz = pytz.timezone('Pacific/Auckland')
    
    # Localize the datetime object to UTC
    dt_utc = dt.astimezone(utc_tz)
    
    # Convert the UTC datetime to New Zealand Time
    dt_nz = dt.astimezone(nz_tz)
    
    # Format the datetime objects into string formats
    formatted_time_utc = dt.strftime('%H:%M : %d-%m-%Y UTC')
    formatted_time_nz = dt_nz.strftime('%H:%M : %d-%m-%Y NZT')
    
    output_string = f"The launch window starts at {formatted_time_utc} ({formatted_time_nz}).  \n\n"
    
    return output_string

#Load comments replied to from file
if not os.path.isfile("comments_replied_to.txt"):
    comments_replied_to = []
else:
    with open("comments_replied_to.txt", "r") as f:
       comments_replied_to = f.read()
       comments_replied_to = comments_replied_to.split("\n")
       comments_replied_to = list(filter(None, comments_replied_to))

#Function to save comments replied to
def exit_handler():
    print("Exiting")
    with open("comments_replied_to.txt", "w") as f:
        for comment_id in comments_replied_to:
            f.write(comment_id + "\n")
    print("Saved comments replied to")

#Main loop to search for comments
try:
        #Recieving stream of comments from subreddit (real time comments + last 100 when initialized)
        for comment in subreddit.stream.comments():
            print("Found new comment")
            if comment.id not in comments_replied_to:
                print("Comment not replied to yet")
                found_comment = commentPattern.search(comment.body)
                if found_comment:
                    try:
                        print("Found a comment asking about Rocket Lab's next launch")
                        print(comment.body)
                        #Get the position of the comment in the comment body.
                        found_comment_position = found_comment.start()
                        
                        #Searching for the matches of the rocket name and location in the comment
                        #It only searches for mentions after the main pattern begins in order to prevent unrelated rocket/location...
                        #...mentions earlier in the comment being picked up as the rocket/location
                        rocket_name_match = rocketPattern.search(comment.body,found_comment_position)
                        rocket_name = rocket_name_match.group().capitalize() if rocket_name_match else None
                        location_nz_name_match = locationNZPattern.search(comment.body,found_comment_position)
                        location_us_name_match = locationUSPattern.search(comment.body,found_comment_position)
                        

                        #if the comment contains both locations, disregard the location.
                        # this is assuming that the comment contains both locations because the user is unsure of the location/asking about either
                        location_id = None
                        if not (location_nz_name_match and location_us_name_match):
                            print("Found a location")
                            if(location_nz_name_match):
                                #Mahia LC1 location id
                                print("Comment mentions mahia")
                                location_id = "10"
                            if(location_us_name_match):
                                
                                #Wallops LC2 location id
                                print("Comment mentions wallops")
                                location_id = "21"
                        launchInfo = get_next_launch(rocket_name,location_id)
                        launchInfo += "Bleep Bloop, I'm a bot."
                        #below commented out for testing
                        # if comment.author.name != reddit.user.me().name:
                        comment.reply(launchInfo)
                        comments_replied_to.append(comment.id)
                        print("Replied to:", comment.id)
                    except Exception as e:
                        print("Error replying to comment:", e)
                        exit_handler()
            else:
                print("Already replied to comment")
                print(comment.body)
except KeyboardInterrupt:
    print("Stopped by user")
    exit_handler()






            
    
            
                
                    
                    
                        