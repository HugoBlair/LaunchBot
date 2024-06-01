import os
import re
import praw

reddit = praw.Reddit('launchBot')

subreddit = reddit.subreddit("pythonforengineers")

commentPattern = re.compile("When is rocketlab's next launch?", re.IGNORECASE)

if not os.path.isfile("comments_replied_to.txt"):
    comments_replied_to = []
else:
    with open("comments_replied_to.txt", "r") as f:
       comments_replied_to = f.read()
       comments_replied_to = comments_replied_to.split("\n")
       comments_replied_to = list(filter(None, comments_replied_to))


for submission in subreddit.new(limit=10):
    for comment in submission.comments:
        
        print("Found new comment")
        if commentPattern.search(comment.body):
            print("Found a comment asking about Rocket Lab's next launch")
            if(comment.id not in comments_replied_to):
                comments_replied_to.append(comment.id)
                print("Replied to:"+comment.id)
                comment.reply("Rocket Lab's next launch is scheduled for August 19th, 2019. You can find more information on the Rocket Lab website: https://www.rocketlabusa.com/launch/")


with open("comments_replied_to.txt", "w") as f:
    for comment_id in comments_replied_to:
        f.write(comment_id + "\n")
            
    
            
                
                    
                    
                        