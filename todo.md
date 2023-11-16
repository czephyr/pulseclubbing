todo:
x To scrape: https://www.30formiche.it/#events
- integrate streaming platforms links or embeds (see fanfulla artists_links field)
- Scrape RA links on tg bot
x fix that if the date is not correct format when given to bot everything fails
    x thats also true sometimes when openai answers with a wrongly formatted date
x make available and link next month page 
x We are now scraping the whole month for Fanfulla, but at the moment we need to insert the link manually
- Manual ig input on tg bot: Handle the case where the IG shortcode needs to be inserted 'cause the post is new
- When a new event gets added (on tg bot or by cron) send a msg to tg group [maybe use a job queue and send them asyncronously in peak day hrs when found by cronjob at 6am] 
x block the bot to some telegram ids
- Handle multiple events in the same description
rollout:
x buy domain
x add telegram group to website
- stick qrs in real world places