# Rocket Launch Bot

LaunchBot is a Reddit bot designed to respond to user comments with information about upcoming rocket launches. It utilizes the Reddit API, along with data from TheSpaceDev's Launch Library 2 API, to provide users with details about Rocket Lab's next rocket launch.

## Features
- **Customized Responses**: Searches for the latest launch in a specific location, or for a specific rocket based on the user's comment
- **Live Reddit Integration**: Continually monitors specified subreddits for user comments containing queries about rocket launches.
- **API Interaction**: Retrieves data from TheSpaceDev's Launch Library 2 API
- **Regex Pattern Matching**: Identifies relevant phrases in user comments using regular expressions.
- **Time Conversion**: Converts launch times from UTC to local time zone for display.
- **Cloud Deployment**: LaunchBot is currently operational and deployed to an AWS EC2 instance for 24/7 operations.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/LaunchBot.git

2a. Install Dependencies
  ```bash
  pip3 install -r requirements.txt
  ```

or

2b. Manually install Dependencies
  ```bash
  pip3 install praw
  ```

  ```bash
  python -m pip3 install requests
  ```

  ```bash
  pip3 install pytz
 ```

3. Configure your praw.ini file and place in repository folder (example)
![image](https://github.com/HugoBlair/LaunchBot/assets/118417835/bf46beaf-0460-4d8c-b51b-2e9e76d4c47f)

## Running

  ```bash
  python3 LaunchBot.py
  ```

## Testing

Unit tests are provided to ensure the functionality and correctness of the bot. Run the tests using:

  ```bash
  python -m unittest TestLaunchBot.py
  ```

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests if you encounter any bugs or have suggestions for improvements.
I made this as a fun project to develop my python skills, so I would appreciate any comments/feedback!
