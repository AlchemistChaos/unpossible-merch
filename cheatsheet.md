

prompt for generating images
-- use logos, prefer pngs or svgs... try to use black and white colors only for tshirts
-- use name of event on tshirt

invite cohost


Email and password is the same for all platforms.

email: riverscreation+ralph@gmail.com
pw: UnpossibleMerch101!

event to create t-shirt images for:
https://luma.com/hh5k4ahp

direction: make 6 t-shirt decisions
1 really crisp and simple 
2 funny / memes
3 using sponsor logos

fourth wall login

Platforms to use:

https://fourthwall.com/
https://luma.com


Event link is:
https://luma.com/hh5k4ahp


If you need to make new email accounts then use this gmail account for registration:

email: [REDACTED - see .env]
password: [REDACTED - see .env]

gemini api key: [REDACTED - see .env]


Hey, so basically we're at a hackathon and we need to build an MVP as fast as possible for this product that we're working on. We're going to be using Ralph Loop and we're going to be using OpenAI credits to basically do most of the work here. The product idea is essentially a one-click merchandise agent for events, very specifically Luma events. What we want to do is allow the user to be able to invite the merchandise agent. The merchandise agent is called Unpossible Merch. It's a spin off of the meme that Ralph Wiggum would say: "Me speak mean or no English. That's impossible." Once the user invites Unpossible Merch as a co-host for their Luma event, what the Unpossible Merch agent should do is scan the event and find relevant information about the event, including:
- the event name
- the theme of the event
- the types of attendees that are coming along
- the existing sponsors  What it should do is generate merchandise, specifically t-shirt graphic ideas for that event. Think of it like this: it should generate about 10 ideas for the event when it comes to t-shirts. Each one needs to be a range. Some t-shirt ideas need to be really sleek, very minimalistic, maybe it's just got a few words or a slogan or the event name and something like that. Others are a bit more like a typical NASCAR-style t-shirt, where it's got all the logos of sponsors there, and the event name there, etc. What we want the agent to do is:
1. First, the agent must design these concepts and write them down as briefs, like text briefs.
2. Then it should generate them as images.
3. Once it's generated enough as images, it should then log into a t-shirt printing company I have uploaded the details of one already, which is called fourthworld.com.
4. It should go on fourthworld.com and create the t-shirts there.
5. It should select one of the base t-shirts on fourthworld.com, upload the image to fullflow.com, save it, and then save it.
6. Fourthwall.com also has a website page where you can actually sell the t-shirt on the website, so it should also do that.
7. It should use fourthwall.com to launch a site, and the site specifically is for selling the t-shirt.
8. Once it's got the site and it's got the t-shirt, it should then send promotional messages, which it then sends as blasts on Luma.  That's why we invited that as a co-host on Luma, because it's going to write a promotional message before, during, and after the event and send it on Luma. For the purpose of the demo, we basically want to show we want all of this already executed. Once the demo runs, it automatically will just generate the designs and make the post, the blast post, on Luma. Then the user, an event attendee, can just go there, click Attend, click Not Attend, click on the blast link, see the page load up for the website, and then basically go and make a purchase.

fyi at the hackathon, i cannot edit the code, we need to one shot all of this, so once i hit start/run, it must execute all of this end to end itself.

we're using ralph loop to basically test and iterate on this idea until it's actually built. so what i want you to do is keep building and testing until this actually works end to end.

the final product i should be able to see an event, see all the tshirts it generated on fourthwall, see the links to the tshirts on the luma, click a link, and buy a tshirt.