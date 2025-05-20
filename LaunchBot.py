from datetime import datetime
import os
import re
import praw
import pytz
import requests
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
def setup_logger():
    # Create logger
    logger = logging.getLogger('LaunchBot')
    logger.setLevel(logging.INFO)

    # Create file handler for logging to a file (max 5MB, keep 3 backup files)
    file_handler = RotatingFileHandler('launchbot.log', maxBytes=5*1024*1024, backupCount=3)
    file_handler.setLevel(logging.INFO)

    # Create console handler for logging to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Set up the logger
logger = setup_logger()

# Accessing the reddit API details from my praw.ini file (which is in the same directory as the script)
# This information is kept private and not included in the repository
logger.info("Initializing Reddit API connection")
try:
    reddit = praw.Reddit('launchBot')
    logger.info("Successfully connected to Reddit API")
except Exception as e:
    logger.error(f"Failed to connect to Reddit API: {e}")
    exit(1)

# Choosing the subreddits to search for comments in
subreddit = reddit.subreddit("rocketlab+rklb")
logger.info(f"Monitoring subreddits: {subreddit.display_name}")

# Regex patterns to search for comments with
commentPattern = re.compile(r"when(\sis\s|\sdoes\s|\'s\s|\sare\s|\swill\s)(\S*\s){0,4}launch(?!\scomplex\s\d)",
                            re.IGNORECASE)
rocketPattern = re.compile(r"Electron|Haste|Neutron", re.IGNORECASE)
locationNZPattern = re.compile(r"NZ|New Zealand|Mahia|Launch Complex 1|LC1", re.IGNORECASE)
locationUSPattern = re.compile(r"US|United States|Virginia|USA|Wallops|Launch Complex 2|LC2|MARS", re.IGNORECASE)


# Function to get the next launch from the API
def get_next_launch(rocket=None, location=None):
    try:
        url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
        params = {
            "hide_recent_previous": "true",
            "include_suborbital": "true",
            "limit": 1,
            # LSP = Launch Service Provider
            "lsp__id": "147",
            "rocket__configuration__name": rocket,
            "location__ids": location
        }
        response = requests.get(url, params)
        logger.info(f"API request made to: {response.url}")
        launchInfo = extract_launch_info(response)

        # Handling cases where there are no launches scheduled with different query types
        if launchInfo == None:
            if (rocket and not location):
                launchInfo = f"Rocketlab doesn't have any official launches scheduled for {rocket} at the moment  \n"
                logger.info(f"No launches found for rocket: {rocket}")
            elif (location and not rocket):
                launchInfo = f"Rocketlab doesn't have any official launches scheduled at {location} at the moment  \n"
                logger.info(f"No launches found at location ID: {location}")
            elif (rocket and location):
                launchInfo = f"Rocketlab doesn't have any official launches scheduled for {rocket} at {location} at the moment  \n"
                logger.info(f"No launches found for rocket: {rocket} at location ID: {location}")
            else:
                launchInfo = f"Rocketlab doesn't have any official launches scheduled at the moment.  \n"
                logger.info("No launches found with general query")
        return launchInfo

    except Exception as e:
        logger.error(f"Error retrieving launch information: {e}", exc_info=True)
        exit_handler()


# Function to extract the launch information from the API response
def extract_launch_info(response):
    if response.status_code == 200:
        launches = response.json().get("results", [])
        if launches:
            launch = launches[0]
            launch_window_start = launch.get("window_start")
            rocket_name = launch.get("rocket", {}).get("configuration", {}).get("name")
            mission_name = launch.get("mission", {}).get("name")
            mission_description = launch.get("mission", {}).get("description")
            agencies = launch.get("mission").get("agencies", [])
            pad_name = launch.get("pad", {}).get("name")
            pad_location_name = launch.get("pad", {}).get("location", {}).get("name")
            agency_launch_attempt_count_year = launch.get("agency_launch_attempt_count_year", {})
            agency_launch_attempt_count = launch.get("agency_launch_attempt_count", {})
            agencies_info = ""
            # Handling the case where there is multiple agencies involved in the mission
            for agency in agencies:
                agency_name = agency.get("name")
                agency_abbrev = agency.get("abbrev")
                if (agency_abbrev):
                    agencies_info += agency_name + " (" + agency_abbrev + "),"
                else:
                    agencies_info += agency_name + ","
            agencies_info = agencies_info.rstrip(", ")

            launch_info = (
                f"Rocket Lab is launching {rocket_name} next from {pad_name} ({pad_location_name}).  \n\n"
                f"{convert_time(launch_window_start)}"
                # If multiple agencies are involved in the mission, it is known as a "Rideshare" mission
                f"They are launching {mission_name} {'for' if len(agencies) == 1 else 'a rideshare mission for '} {agencies_info}.  \n\n"
                f"The mission is stated as follows: {mission_description}  \n\n"
                f"This is launch #{agency_launch_attempt_count_year} this year, and launch #{agency_launch_attempt_count} overall.  \n\n"
            )
            logger.info(f"Found launch information: {rocket_name} for {mission_name}")
            return launch_info
        logger.warning("No upcoming launches found in API response")
        return None


def convert_time(input_time):
    try:
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

        logger.debug(f"Converted launch time: {formatted_time_utc} ({formatted_time_nz})")

        output_string = f"The launch window starts at {formatted_time_utc} ({formatted_time_nz}).  \n\n"

        return output_string
    except ValueError as e:
        logger.error(f"Invalid time format: {e}", exc_info=True)
        return "I cannot retrieve the launch time at the moment. \n\n"


# Load comments replied to from file
if not os.path.isfile("comments_replied_to.txt"):
    logger.info("Creating new comments_replied_to.txt file")
    comments_replied_to = []
else:
    with open("comments_replied_to.txt", "r") as f:
        logger.info("Loading existing comments_replied_to.txt")
        comments_replied_to = f.read()
        comments_replied_to = comments_replied_to.split("\n")
        comments_replied_to = list(filter(None, comments_replied_to))
        logger.info(f"Loaded {len(comments_replied_to)} previously replied comments")


# Function to save comments replied to
def exit_handler():
    logger.info("Exiting application and saving comment history")
    with open("comments_replied_to.txt", "w") as f:
        for comment_id in comments_replied_to:
            f.write(comment_id + "\n")
    logger.info(f"Saved {len(comments_replied_to)} comment IDs to file")

    search_for_comments()


def search_for_comments():
    # Main loop to search for comments
    try:
        logger.info("Starting LaunchBot comment monitoring")
        # Receiving stream of comments from subreddit (real time comments + last 100 when initialized)
        bot_username = reddit.user.me().name
        logger.info(f"Bot running as: {bot_username}")

        for comment in subreddit.stream.comments():
            logger.debug(f"Found new comment ID: {comment.id}")
            if comment.author.name != bot_username:
                if comment.id not in comments_replied_to:
                    found_comment = commentPattern.search(comment.body)
                    if found_comment:
                        try:
                            logger.info(f"Found comment asking about launch from user: {comment.author.name}")
                            logger.debug(f"Comment text: {comment.body}")
                            # Get the position of the comment in the comment body.
                            found_comment_position = found_comment.start()

                            # Searching for the matches of the rocket name and location in the comment
                            # It only searches for mentions after the main pattern begins in order to prevent unrelated rocket/location...
                            # ...mentions earlier in the comment being picked up as the rocket/location
                            rocket_name_match = rocketPattern.search(comment.body, found_comment_position)
                            rocket_name = rocket_name_match.group().capitalize() if rocket_name_match else None
                            if rocket_name:
                                logger.info(f"Rocket name detected: {rocket_name}")

                            location_nz_name_match = locationNZPattern.search(comment.body, found_comment_position)
                            location_us_name_match = locationUSPattern.search(comment.body, found_comment_position)

                            # if the comment contains both locations, disregard the location.
                            # this is assuming that the comment contains both locations because the user is unsure of the location/asking about either
                            location_id = None
                            if not (location_nz_name_match and location_us_name_match):
                                if location_nz_name_match:
                                    # Mahia LC1 location id
                                    logger.info("Location detected: Mahia/New Zealand")
                                    location_id = "10"
                                if location_us_name_match:
                                    # Wallops LC2 location id
                                    logger.info("Location detected: Wallops/USA")
                                    location_id = "21"

                            launchInfo = get_next_launch(rocket_name, location_id)
                            launchInfo += "Bleep Bloop, I'm a bot."

                            comment.reply(launchInfo)
                            comments_replied_to.append(comment.id)
                            logger.info(f"Successfully replied to comment ID: {comment.id}")
                        except Exception as e:
                            logger.error(f"Error replying to comment ID {comment.id}: {e}", exc_info=True)
                            exit_handler()
                else:
                    logger.debug(f"Already replied to comment ID: {comment.id}")
            else:
                logger.debug(f"Comment from bot, ignoring: {comment.id}")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (KeyboardInterrupt)")
        exit_handler()
    except Exception as e:
        logger.critical(f"Unexpected error in main loop: {e}", exc_info=True)
        exit_handler()


if __name__ == "__main__":
    search_for_comments()