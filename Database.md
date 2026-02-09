# Database setup 101 (sort of)

## !!! NOTE: !!!

### I'd highly recommend that you learn the basics of not only docker but docker compose, I'd also recommend not using docker desktop as it's a pain in the ass (and i lost my whole database to a bug)

### Remember to always use strong passwords and keep a good "cyber hygiene" ([Explanation of the expression](https://www.proofpoint.com/us/threat-reference/cyber-hygiene#:~:text=Cyber%20hygiene%2C%20or%20cybersecurity%20hygiene,from%20cyber-attacks%20and%20theft.))

To make the bot work properly you need a Postgre SQL database, you'll also need an admin platform (in my case PgAdmin). In your admin panel you need to connect your database server to the panel and then make a "table" with the name info (a table is basically just an excel file but in the SQL programming language). This table needs to have the following columns: (this is caps sensitive)

- guild_id (needs to be prime key and not NULL)
- log_id (big int)
- wlc_id (big int)
- bye_id (big int)
- wlc_pic (text)
- bye_pic (text)
- wlc_msg (text)
- bye_msg (text)
- wlc_title (text)
- bye_title (text)
- wlc_hex (text)
- bye_hex (text)
- prefix (text)
- raid_response_enabled (boolean) (not NULL) (default set to false)
- notes (text) (Optional)

## Additional links

- [How to create a docker-compose setup with PostgreSQL and pgAdmin4](https://youtu.be/qECVC6t_2mU?si=if9DEovqKu07_V4V)
- [Docker Compose will BLOW your MIND!! (a tutorial)](https://youtu.be/DM65_JyGxCo?si=t2O7dd8gWNboVm3N)
- [Learn Docker in 7 Easy Steps - Full Beginner's Tutorial](https://youtu.be/gAkwW2tuIqE?si=fVkdp3KHfZjrWy6B)

Helpful tools that I love:

- [Dockge](https://github.com/louislam/dockge) (used to manage docker compose containers)
