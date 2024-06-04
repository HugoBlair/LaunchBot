import unittest
from unittest.mock import patch, MagicMock
import re
from datetime import datetime
import pytz

# Assuming your functions are in a file named rocket_launch_bot.py
from LaunchBot import (
    get_next_launch, 
    extract_launch_info, 
    convert_time, 
    commentPattern, 
    rocketPattern, 
    locationNZPattern, 
    locationUSPattern
)

class TestLaunchBot(unittest.TestCase):
    def setUp(self):
        # Example setup if needed
        self.example_api_response = {
            "results": [
                {
                    "window_start": "2024-06-01T12:00:00Z",
                    "rocket": {
                        "configuration": {
                            "name": "Electron"
                        }
                    },
                    "mission": {
                        "name": "Test Mission",
                        "description": "A test mission",
                        "agencies": [{"name": "NASA", "abbrev": "NASA"}]
                    },
                    "pad": {
                        "name": "LC-1",
                        "location": {
                            "name": "Mahia Peninsula"
                        }
                    },
                    "agency_launch_attempt_count_year": 5,
                    "agency_launch_attempt_count": 15
                }
            ]
        }
    @patch('LaunchBot.requests.get')
    def test_get_next_launch(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.example_api_response
        
        result = get_next_launch(rocket="Electron", location="10")
        self.assertIn("Rocket Lab is launching Electron next from LC-1 (Mahia Peninsula).", result)
    
    def test_extract_launch_info(self):
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = self.example_api_response

        result = extract_launch_info(response)
        self.assertIn("Rocket Lab is launching Electron next from LC-1 (Mahia Peninsula).", result)

    def test_convert_time(self):
        input_time = "2024-06-01T12:00:00Z"
        expected_output = (
            "The launch window starts at 12:00 : 01-06-2024 UTC (00:00 : 02-06-2024 NZT).  \n\n"
        )
        result = convert_time(input_time)
        self.assertEqual(result, expected_output)

    def test_convert_time_2(self):
        input_time = "2024-06-01T04:00:00Z"
        expected_output = (
            "The launch window starts at 04:00 : 01-06-2024 UTC (16:00 : 01-06-2024 NZT).  \n\n"
        )
        result = convert_time(input_time)
        self.assertEqual(result, expected_output)

    def test_convert_time_invalid_input(self):
        input_time = "invalid"
        expected_output = "Invalid time format"
        result = convert_time(input_time)
        self.assertRaises(ValueError, result)

    def test_comment_patterns(self):
        
        test_comments = ("When is the next launch of Electron from NZ?",
                        "When's Electron Launching from NZ?",
                        "When's NZ launching Electron?",
                        "When will electron launch from NZ?",
                        "When are they launching Electron from NZ?"
                        
        )
        for test_comment in test_comments:
            self.assertIsNotNone(commentPattern.search(test_comment))
            self.assertIsNotNone(rocketPattern.search(test_comment))
            self.assertIsNotNone(locationNZPattern.search(test_comment))
            self.assertIsNone(locationUSPattern.search(test_comment))

    def test_comment_patterns2(self):
        
        test_comments = ("When is the next launch of Electron from US?",
                        "When's Electron Launching from US?",
                        "When's US launching Electron?",
                        "When will electron launch from US?",
                        "When are they launching Electron from US?"
                        
        )
        for test_comment in test_comments:
            self.assertIsNotNone(commentPattern.search(test_comment))
            self.assertIsNotNone(rocketPattern.search(test_comment))
            self.assertIsNone(locationNZPattern.search(test_comment))
            self.assertIsNotNone(locationUSPattern.search(test_comment))

    def test_comment_patterns_invalid(self):
        
        test_comments = ("When is launch complex 3 being built?",
                        "When's the time?",
                        "are they launching?",
                        "Is there a launch"
                        
        )
        for test_comment in test_comments:
            self.assertIsNone(commentPattern.search(test_comment))
            self.assertIsNone(rocketPattern.search(test_comment))
            self.assertIsNone(locationNZPattern.search(test_comment))
            self.assertIsNone(locationUSPattern.search(test_comment))


        
        
                        
        