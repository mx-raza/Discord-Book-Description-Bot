import random
import asyncio
import aiohttp
import json
from discord import Embed
import DiscordUtils
from discord.ext.commands import Bot
import os
from keep_alive import keep_alive
from requests_html import HTMLSession
import re
from replit import db
from urllib.parse import quote_plus
from datetime import date


BOT_PREFIX = ("!", "?b")
TOKEN = os.environ.get("DISCORD_BOT_SECRET")
client = Bot(command_prefix=BOT_PREFIX)

def randomColor():
    random_number = random.randint(0,16777215)
    return random_number

def replaceHtmlTags(html):
    boldnitalicEnd = re.compile('( ?</i( .*?|)?> ?</b( .*?|)?> ?| ?</b( .*?|)?> ?</i( .*?|)?> ?)')
    html = re.sub(boldnitalicEnd, '*** ', html)
    boldnitalicStart = re.compile(' ?<i( .*?|)?> ?<b( .*?|)?> ?| ?<b( .*?|)?> ?<i( .*?|)?> ?')
    html = re.sub(boldnitalicStart, ' *', html)
    italicsEnd = re.compile(' ?</i( .*?|)?> ?')
    html = re.sub(italicsEnd, '* ', html)
    italicsStart = re.compile(' ?<i( .*?|)?> ?')
    html = re.sub(italicsStart, ' *', html)
    boldEnd = re.compile(' ?</b( .*?|)?> ?')
    html = re.sub(boldEnd, '** ', html)
    boldStart = re.compile(' ?<b( .*?|)?> ?')
    html = re.sub(boldStart, ' **', html)
    tags = re.compile('<.*?>')
    html = re.sub(tags, '', html)
    html = html.replace('\\n', '\n')
    return html

def replaceSHtmlTags(html):
    boldnitalicEnd = re.compile('( ?<\\\\/i( .*?|)?> ?<\\\\/b( .*?|)?> ?| ?<\\\\/b( .*?|)?> ?<\\\\/i( .*?|)?> ?)')
    html = re.sub(boldnitalicEnd, '*** ', html)
    boldnitalicStart = re.compile(' ?<i( .*?|)?> ?<b( .*?|)?> ?| ?<b( .*?|)?> ?<i( .*?|)?> ?')
    html = re.sub(boldnitalicStart, ' ***', html)
    italicsEnd = re.compile(' ?<\\\\/i( .*?|)?> ?')
    html = re.sub(italicsEnd, '* ', html)
    italicsStart = re.compile(' ?<i( .*?|)?> ?')
    html = re.sub(italicsStart, ' *', html)
    boldEnd = re.compile(' ?<\\\\/b( .*?|)?> ?')
    html = re.sub(boldEnd, '** ', html)
    boldStart = re.compile(' ?<b( .*?|)?> ?')
    html = re.sub(boldStart, ' **', html)
    tags = re.compile('<.*?>')
    html = re.sub(tags, '', html)
    html = html.replace('\\n', '\n')
    return html

def getBookId(SearchQuery):
    session = HTMLSession()
    r = session.get("https://app.thestorygraph.com/browse?search_term="+quote_plus(SearchQuery))
    searchResult=r.html.find("div.book-pane-content", first=True)
    if(searchResult is None):
        return "No results found."
    results = filter(lambda x: x.startswith("/books/") and not(x.endswith('editions')), searchResult.links)
    bookID = list(results)[0][1:]
    return bookID

def getTitle(r):
    title=r.html.find(".book-title-author-and-series", first=True)
    title=title.find("h3",first=True).text+" by "+title.find("p", first=True).text
    return title

def getDescription(r):
    script=list(filter(lambda x: x.text.startswith("$('.read-more-btn')"), r.html.find("script")))[0].text
    preffix = re.compile('.*?Description')
    script = re.sub(preffix, '', script)
    suffix = re.compile('\'\\).*')
    script = re.sub(suffix, '', script)
    script = replaceSHtmlTags(script)
    return script

def getImage(r):
    try:
        return r.html.find("div.book-cover img", first=True).attrs["src"]
    except AttributeError:
        return ""

def getContentWarning(r):
    try:
        cw = r.html.find("div.content-warnings-information", first=True).html
        cw = replaceHtmlTags(cw)
        return cw
    except AttributeError:
        return "No Content Warnings Found"

def getTop5Moods(r):
    try:
        moods = ", ".join([x.text for x in r.html.find("div.moods-list-reviews", first=True).find("span")[:10:2]])
        return moods
    except AttributeError:
        return "No Moods Reviews Found"

def getPace(r):
    try:
        return r.html.find("div.paces-reviews", first=True).text
    except AttributeError:
        return "No Pace Reviews Found"

def getRating(r):
    try:
        rating = r.html.find("span.average-star-rating", first=True).text
        val = float(rating)
        stars = "★"*int(val)
        decimal = val-int(val)
        if(decimal < 0.25):
            stars += "✰"
        elif(decimal < 0.75):
            stars += "✫"
        else:
            stars += "★"
        stars += "✰"*(5-len(stars))
        return rating+" "+stars
    except AttributeError:
        return "No rating found"

# @client.event
# async def on_raw_reaction_add(payload):
#     message_id = payload.message_id
#     if(payload.emoji.name == 'eyes'):
#         pass

# @client.event
# async def on_raw_reaction_remove(payload):
#     message_id = payload.message_id
#     pass

@client.command(
    name="BookLookup",
    help="Search for a book using Title, Author, or ISBN.",
    aliases=["bl", "booklookup"],
    pass_context=True,
  )
async def BookLookup(ctx):
    msg=ctx.message.content.split()
    try:
        if(len(msg)>=2):
            bookID = getBookId(" ".join(msg[1:]))
            if(bookID == "No results found."):
                await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\"."))
            else:
                session = HTMLSession()
                r = session.get("https://app.thestorygraph.com/"+bookID)

                embed=Embed(title=getTitle(r), description="", color=randomColor())
                embed.add_field(name="Content Warning", value="||"+getContentWarning(r)+"||", inline=True)
                embed.add_field(name="Moods", value=getTop5Moods(r), inline=True)
                embed.add_field(name="Pace Reviews", value=getPace(r), inline=True)
                embed.set_image(url=getImage(r))
                embed.set_footer(text="Rating: "+getRating(r), icon_url=ctx.author.avatar_url)

                description = getDescription(r)
                if(len(description)>1024):
                    paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, remove_reactions=True)
                    paginator.add_reaction('🔐', "lock")
                    paginator.add_reaction('⏪', "back")
                    paginator.add_reaction('⏩', "next")
                    embeds = []
                    subDesc = description
                    while True:
                        e = Embed().from_dict(embed.to_dict())
                        end = subDesc[:1024].rfind(" ")
                        e.description = subDesc[:end]
                        embeds.append(e)
                        if(len(subDesc) < 1024):
                            break
                        subDesc = subDesc[end:]
                    
                    await paginator.run(embeds)
                else:
                    embed.description = description
                    await ctx.send(embed=embed)
        else:
            raise Exception("Does not fit usage.")
    except Exception as e:
        await ctx.send("Usage: ![booklookup|bl] <Title, Author or ISBN>")
        raise e

@client.command(
    name="ToRead",
    help="Add to reading list using Title, Author, or ISBN.",
    aliases=["tr", "toread"],
    pass_context=True,
  )
async def AddToReadingList(ctx):
    msg=ctx.message.content.split()
    UID=str(ctx.author.id)
    try:
        if(len(msg)>=2):
            if(len(db.prefix(UID))==0):
                db[UID]={}
            bookID=getBookId(" ".join(msg[1:]))
            if(bookID != "No results found."):
                if(bookID in db[UID].keys()):
                    db[UID][bookID]["status"]="TBR"
                    title = db[UID][bookID]["title"]
                    await ctx.send(embed=Embed(description="Status of "+title+" changed to TBR."))
                else:
                    session = HTMLSession()
                    r = session.get("https://app.thestorygraph.com/"+bookID)
                    title = getTitle(r)
                    db[UID][bookID]={
                        "title": title,
                        "status": "TBR",
                        "readDate": ""
                    }
                    await ctx.send(embed=Embed(description="Book Titled \""+title+"\" added to TBR list."))
            else:
                await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\"."))
        else:
            raise Exception("Does not fit usage.")
    except Exception as e:
        await ctx.send("Usage: ![toread|tr] <Title, Author, or ISBN>")
        raise e

@client.command(
    name="RemoveBook",
    help="Remove from reading list using Title.",
    aliases=["rb", "removebook"],
    pass_context=True,
  )
async def RemoveFromReadingList(ctx):
    msg=ctx.message.content.split()
    UID=str(ctx.author.id)
    deleted = False
    try:
        if(len(msg)>=2):
            if(len(db.prefix(UID))==1):
                books=db[UID]
                for book in books.keys():
                    if(books[book]["title"].lower().__contains__(" ".join(msg[1:]).lower())):
                        await ctx.send(embed=Embed(description="Book Titled \""+books[book]["title"]+"\" removed from the Reading List."))
                        del db[UID][book]
                        deleted = True
                        break;
                if(not(deleted)):
                    await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\" in the Reading List."))
            else:
                await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\" in the Reading List."))
        else:
            raise Exception("Does not fit usage.")
    except Exception as e:
        await ctx.send("Usage: ![removebook|rb] <Title>")
        raise e

@client.command(
    name="MarkRead",
    help="Mark book as read using Title.",
    aliases=["mr", "markread"],
    pass_context=True,
  )
async def MarkAsRead(ctx):
    msg=ctx.message.content.split()
    UID=str(ctx.author.id)
    changed = False
    try:
        if(len(msg)>=2):
            if(len(db.prefix(UID))==1):
                books=db[UID]
                for book in books.keys():
                    if(books[book]["title"].lower().__contains__(" ".join(msg[1:]).lower())):
                        await ctx.send(embed=Embed(description="Book Titled \""+books[book]["title"]+"\" marked as Read in the Reading List."))
                        db[UID][book]["status"] = "Read"
                        db[UID][book]["readDate"] = date.today().strftime("%d-%b-%Y")
                        changed = True
                        break;
                if(not(changed)):
                    await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\" in the Reading List."))
            else:
                await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\" in the Reading List."))
        else:
            raise Exception("Does not fit usage.")
    except Exception as e:
        await ctx.send("Usage: ![markread|mr] <Title>")
        raise e

@client.command(
    name="ReadingCurrently",
    help="Mark book as reading is currently in progress using Title.",
    aliases=["rc", "reading"],
    pass_context=True,
  )
async def ReadingCurrently(ctx):
    msg=ctx.message.content.split()
    UID=str(ctx.author.id)
    changed = False
    try:
        if(len(msg)>=2):
            if(len(db.prefix(UID))==1):
                books=db[UID]
                for book in books.keys():
                    if(books[book]["title"].lower().__contains__(" ".join(msg[1:]).lower())):
                        await ctx.send(embed=Embed(description="Book Titled \""+books[book]["title"]+"\" marked as Reading in the Reading List."))
                        db[UID][book]["status"] = "Reading"
                        changed = True
                        break;
                if(not(changed)):
                    await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\" in the Reading List."))
            else:
                await ctx.send(embed=Embed(description="No results found for \""+" ".join(msg[1:])+"\" in the Reading List."))
        else:
            raise Exception("Does not fit usage.")
    except Exception as e:
        await ctx.send("Usage: ![reading|rc] <Title>")
        raise e

@client.command(
    name="GetReadingList",
    help="Get the whole Reading List of the User.",
    aliases=["gl", "getreadinglist"],
    pass_context=True,
  )
async def GetReadingList(ctx):
    UID=str(ctx.author.id)
    try:
        if(len(db.prefix(UID))==1):
            books=db[UID]
            readingList=""
            for book in books.keys():
                readingList+="Title: "+books[book]["title"]+" Status: "+books[book]["status"]
                if(books[book]["status"]=="Read"):
                    readingList+=" on "+books[book]["readDate"]
                readingList+="\n"
            await ctx.send(embed=Embed(description="Reading List:\n"+readingList))
        else:
            await ctx.send(embed=Embed(description="No Reading List Found."))
    except Exception as e:
        await ctx.send("Usage: ![getreadinglist|gl]")
        raise e

@client.event
async def on_ready():
    # await client.change_presence(game=Game(name="with humans"))
    print("Logged in as " + client.user.name)

async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)

keep_alive()

client.run(TOKEN)