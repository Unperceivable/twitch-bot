#!/usr/bin/python
__author__ = 'Unperceivable'
__module_name__ = "TwitchBotHandler"
__module_version__ = "v2.0"
__module_description__ ="TwitchBotHandler"

import json
import xchat
import urllib2
import collections
import os
import time
import pickle
from datetime import datetime, timedelta, date
from operator import itemgetter

channelBots=dict()

def on_connect(word, word_eol, userdata):
    if word[1] not in channelBots.values():
        channelBots[word[1]]=TwitchBot(str(word[1])[1:])
        xchat.prnt("\00304 successfully connected to "+ word[1] +" \003")
        channelBots[word[1]].on_connect(word, word_eol, userdata)

#on message callback , check if message is command and executes command if valid/privileges are met
def on_message(word, word_eol, userdata):
    try:
        channelBots[xchat.get_info("channel")].on_message(word, word_eol, userdata)
    except KeyError:
        on_connect(word,word_eol,userdata)
        channelBots[xchat.get_info("channel")].on_message(word, word_eol, userdata)



def on_op(word, word_eol, userdata):
    try:
        channelBots[xchat.get_info("channel")].on_op(word, word_eol, userdata)
    except KeyError:
        on_connect(word,word_eol,userdata)
        channelBots[xchat.get_info("channel")].on_op(word, word_eol, userdata)


xchat.hook_print('You Join', on_connect)
xchat.hook_print('Channel Message', on_message)
xchat.hook_print('Channel Operator', on_op)

#xchat.hook_print('Connected', on_connect)
#xchat.hook_print('Connecting', on_connect)
#xchat.hook_print('Your Action', on_connect)
#xchat.hook_print('Your Invitation', on_connect)
#hook commands that keep script from sleeping, and trigger on_message and on_join functions when first parameters are met, new meesage or new people enter the channel
#xchat.hook_print('Channel Message', on_message)
#xchat.hook_print('Join', on_join)
#print module name and version in red when loaded

xchat.prnt("\00304" + __module_name__ + __module_version__ + "successfully loaded.\003")

class TwitchBot:

    def __init__(self,user):

        #grab broadcaster name
        self.user = user

        #Uptime Variables
        self.isStreaming=True

        #Polling Variables
        self.isPolling=False
        self.pollingStart=time.time()
        self.pollingTime=2*60
        self.pollOptions=[]
        self.pollVotes={}

        #Filenames in current directory (of this script)
        self.privilegeFilename=os.path.dirname(os.path.abspath('__file__'))+'/'+self.user+"-pFile.p"
        self.commandFilename=os.path.dirname(os.path.abspath('__file__'))+'/'+self.user+"-xFile.p"

        xchat.prnt(self.privilegeFilename)
        xchat.prnt(self.commandFilename)

        #Moderator lists
        self.modL=dict()
        self.modList=[]
        self.superMods=['unperceivable']

        #Command Variables
        self.cmd=dict()
        self.commands=dict()
        self.cmdExcludelist=[]
        self.cmdIgnorelist=[]
        xchat.prnt(str(os.path.exists(self.privilegeFilename) ))
        #Populate create new self.modList if no file availible otherwise load list from file
        if os.path.exists(self.privilegeFilename)==0:
            with open(self.privilegeFilename,'w+') as privilegeFile:
                self.modL['modList']=self.modList
                self.modL['superMods']=self.superMods

                #privilegeFile.write(json.dumps(self.modL))
                pickle.dump(self.modL,privilegeFile)

                xchat.prnt("say current list of mods: "+str(self.modL))
                privilegeFile.close()

        else:
            with open(self.privilegeFilename,'r') as privilegeFile:
                #self.modL=self.convert(json.load(privilegeFile))
                self.modL=pickle.load(privilegeFile)
                self.superMods= self.modL['superMods']
                self.modList = self.modL['modList']
                xchat.prnt("say current list of mods: "+str(self.modL))
                privilegeFile.close()

        xchat.prnt(str(os.path.exists(self.commandFilename) ))
        #Populate  commandList with default values if no file availible otherwise load ductuinary from structure
        if os.path.exists(self.commandFilename)==0:
            with open(self.commandFilename,'w+') as commandFile:

                #dictionary mapping command list to functions executed
                self.cmd['commands']={
                                '!uptime'		: ['uptime'],
                                '!add'			: ['setcmd'],
                                '!remove'		: ['setcmd'],
                                '!commands'		: ['command'],
                                '!set'			: ['setcmd'],
                                '!mods'			: ['mods'],
                                '!poll'			: ['poll'],
                        }
                self.cmd['cmdExcludelist'] =['!mods','!set','!goat','!add','!remove','!poll','!rime','!unperceivable',"!sujoy","!psyc0rn","!caprijake",'!wakeypixel','!m3wk']
                self.cmd['cmdIgnorelist'] =["!pixels" ,"!info" ,"!rankedparty" ,"!leaderboard" ,"!contest"]

                pickle.dump(self.cmd,commandFile)
                xchat.prnt("say list of commands: "+str(self.cmd))
                commandFile.close()

        else:
            with open(self.commandFilename,'r') as commandFile:

                self.cmd=pickle.load(commandFile)
                self.commands=self.cmd['commands']
                self.cmdExcludelist=self.cmd['cmdExcludelist']
                self.cmdIgnorelist=self.cmd['cmdIgnorelist']

                xchat.prnt("say list of commands: "+str(self.cmd))
                commandFile.close()

        #Editable Commands Through Set Command
        cm=set(self.commands.keys())
        #Exclude list from commands to be printed
        cm.update(set(self.commands.keys()))
        cm.difference_update(set(self.cmdExcludelist))
        self.commandList=list(cm)

    #Converts datastructures using utf8 encoding to normal str [u'a'] -> ['a']
    #Credit to stackoverflow.com/questions/1254454/fastest-way-to-convert-a-dicts-keys-values-from-unicode-to-str
    def convert(self,data):
        if isinstance(data, basestring):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict(map(self.convert, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self.convert, data))
        else:
            return data

    #loads data from html webpage as using json (javascript object notation)
    def loadJSON(self,url):
        response = urllib2.urlopen(url)
        obj = json.load(response)
        obj=self.convert(obj)
        return obj

    #Prints how long twitch self.user has been streaming , or if offline
    def uptime(self,word, word_eol, userdata):
        obj = self.loadJSON('https://api.twitch.tv/kraken/streams/' + self.user)


        if(obj["stream"] == None):
            t=self.user + " is not streaming."
            xchat.command("say "+word[0]+' '+t)
            self.isStreaming=False
        else:
            timeFormat = "%Y-%m-%dT%H:%M:%SZ"
            dt=obj["stream"]["created_at"]
            xchat.prnt(str([dt]))
            #startdate = datetime.strptime(dt, timeFormat)
            startdate = datetime.fromtimestamp(time.mktime(time.strptime(dt, timeFormat)))
            currentdate = datetime.utcnow()
            #xchat.prnt(startdate)
            #xchat.prnt(currentdate)
            combineddate = currentdate - startdate - timedelta(microseconds=currentdate.microsecond)
            #xchat.prnt(combinedate)
            t=self.user + " has been streaming for " + str(combineddate)
            xchat.command("say "+word[0]+' '+t)
            self.isStreaming=True

    #prints locally to xchat if "invalid" command is recognized	, also provides functionality to add command.
    def error(self,word, word_eol, userdata):

        if (not self.isStreaming) and (word[1][0].lower() in self.cmdIgnorelist) :
            xchat.command("say "+word[0]+" RevloBot is currently offline and cannot process your request. Visit www.revlo.co/odpixel for further information.")
        else:
            xchat.prnt("say "+word[0]+" command does not exist/is not relevant to me")

    #poll twitch chat for first parameter minutes (otherwise 2) for all other parameters
    def poll(self,word, word_eol, userdata):

        if word[0] in self.modList:

            self.isPolling=True
            self.pollingStart=time.time()

            try:
                self.pollingTime=float(word[1][1])*60
                self.pollOptions=[w.lower() for w in word[1][2:] ]

                xchat.prnt("say time parameter set")

            except ValueError:
                self.pollingTime=2*60
                self.pollOptions=[w.lower() for w in word[1][1:] ]

                xchat.prnt("say no time parameter entered, using 2 minutes")

                xchat.command("say A poll has been created, Type one of the following options to vote (without ' ): "+ str(self.pollOptions)[1:-1] +". You have "+ str(round(float(self.pollingTime)/60,2)) + " minutes to vote. Only your last vote will be counted, Only the exact spelling of the options will be counted, It must be the first word in your message.")
                xchat.prnt("say "+str(self.pollingStart)+" "+str(self.pollingTime)+" "+str(self.pollOptions) )
        else:
            xchat.prnt("say "+word[0]+" the pleb is trying to poll")

    #changes editabled command text - provided moderator credentials
    def setcmd(self,word, word_eol, userdata):
        xchat.prnt("current mod list is: "+ str(self.modList))
        xchat.prnt("set command iussed by " +str(word[0]))
        if word[0] in self.modList or word[0] in self.superMods:
            xchat.prnt("set autherized")
            xchat.prnt("command to be edited: " + word[1][1])
            #xchat.prnt("commands availible to be edited: " + str(commandMsg.keys()))

            if (word[1][0]=='!set' and word[1][1] in self.commands.keys()) and self.commands[word[1][1]][0]=='prnt' :
                self.commands[word[1][1].lower()][1] = ' '.join(word[1][2:])
                xchat.command("say "+word[1][1]+" has been set to: "+self.commands[word[1][1]][1])

            elif (word[1][0]=='!add' or word[1][0]=='!remove') and (word[0] in self.superMods):
                if word[1][1][0]=='!':

                    if word[1][0]=='!add' and len(word[1])>2:
                        wrd=word[1][1].lower()
                        self.commands[wrd]=['prnt',' '.join(word[1][2:])]
                        self.cmdExcludelist.append(wrd)
                        xchat.command("say "+wrd+" has been added to command list and set to: "+self.commands[word[1][1]][1])

                    elif word[1][0]=='!remove':

                        try:
                            wrd=word[1][1].lower()
                            c=self.commands
                            del c[wrd]
                            self.commands=c
                            self.commandList.pop(wrd)
                            xchat.command("say "+wrd+" has been removed from the command set")

                        except KeyError:
                            xchat.prnt("say "+word[1][1]+" was not found to be removed")

                    else:
                        xchat.prnt("something has gone terribly wrong")
                        xchat.prnt(word[1][1])
                else:
                    xchat.prnt("command has irregular formatting")

            else:
                xchat.prnt("say "+word[1][1]+" is not an existing")

            with open(self.commandFilename,'w+') as commandFile:
                self.cmd['commands']=self.commands
                self.cmd['cmdExcludelist']=self.cmdExcludelist
                pickle.dump(self.cmd,commandFile)
                xchat.prnt("commandFile has been updated")
                commandFile.close()

        else:
            xchat.prnt("say "+word[0]+" IS A PLEB!")

    def prnt(self,word, word_eol, userdata):
        xchat.command("say "+ word[0] + " " + self.commands[word[1][0]][1])

    #prints commandList
    def command(self,word, word_eol, userdata):
        xchat.command("say "+word[0]+" These are the commands I respond to: "+ str(self.commandList)[1:-1])

    def mods(self,word, word_eol, userdata):
        if word[0] in self.modList:
            xchat.prnt("say "+word[0]+" Mod List: "+self.modList+" sMod List: "+ self.superMods )

    #on message callback , check if message is command and executes command if valid/privileges are met
    def on_message(self,word, word_eol, userdata):
        s=False

        if word[1][0][0]=='!':
            word[1]=word[1].split()
            try:
                getattr(self,self.commands.get(word[1][0].lower())[0])(word, word_eol, userdata)
            except TypeError:
                self.error(word, word_eol, userdata)
            s=True

        if self.isPolling:
            curTime=time.time()
            xchat.prnt("say "+str(curTime-self.pollingStart))
            xchat.prnt("say "+str(self.pollingTime))
            xchat.prnt("say "+str(curTime-self.pollingStart > self.pollingTime))
            xchat.prnt("say "+str(self.pollOptions))
            if (curTime-self.pollingStart) < self.pollingTime:
                if not s:
                    word[1]=word[1].split()

                if (word[1][0].lower()) in self.pollOptions:
                    self.pollVotes[word[0]]=word[1][0].lower()

            else :
                self.isPolling=False

                pollResults=dict.fromkeys(self.pollOptions,0)
                for val in self.pollVotes.values():
                    pollResults[val]+=1
                xchat.prnt("say "+ str(pollResults))

                pollResults = [(v, k) for k, v in pollResults.iteritems()]
                xchat.prnt("say "+ str(pollResults))

                pollResults = sorted(pollResults, key=itemgetter(0),reverse=True)
                xchat.prnt("say "+ str(pollResults))

                totalVotes=sum(e[0] for e in pollResults)

                try:
                    pollResults=[ str(k) + " : " + str( round( float(v*100)/totalVotes,2))+"%" for (v,k) in pollResults]
                except ZeroDivisionError:
                    xchat.command("say Nobody Voted")
                xchat.command("say The poll is now over, "+ str(totalVotes) +" votes were counted. The voting results are as follows: "+ str(pollResults)[1:-1] )
                self.pollingTime=2*60
                self.pollOptions=[]
                self.pollVotes={}


    #on channel operator status assignment
    def on_op(self,word,word_eol,userdata):
        xchat.prnt(str(word))
        if word[1] not in self.modList:

            with open(self.privilegeFilename,'w') as privilegeFile:

                uml=set(self.modList)
                uml.update([word[1]] )
                self.modList=list(uml)
                self.modL['modList']=self.modList
                xchat.prnt("say mod list updated with"+str(word[1]))
                xchat.prnt("say mod list currently: "+str(self.modL))
                #privilegeFile.write(json.dumps(self.modList))
                pickle.dump(self.modL,privilegeFile)

                privilegeFile.close()


    #on join callback , when twitch api for chatters is updated, check for new moderators to add to list, add and save them otherwise, so nothing (occurs every 10 mins or so)
    def on_connect(self,word,word_eol,userdata):

        #obj = loadJSON('http://tmi.twitch.tv/group/self.user/'+self.user+'/chatters')
        #ml=obj['chatters']['moderators']
        ml=[]
        xchat.prnt("say "+self.commandList)

        for user in xchat.get_list('users'):
            if user.prefix=='@':
                ml.append(user.nick)
        flag=0
        for x in ml:
            if x not in self.modList:
                flag=1
        if flag:
            with open(self.privilegeFilename,'w') as privilegeFile:

                uml=set(self.modList)
                uml.update(set(ml))
                self.modList=list(uml)
                self.modL['modList']=self.modList
                xchat.prnt("say mod list updated with"+str(ml))
                xchat.prnt("say mod list currently: "+str(self.modL))
                #privilegeFile.write(json.dumps(self.modList))
                pickle.dump(self.modL,privilegeFile)

                privilegeFile.close()