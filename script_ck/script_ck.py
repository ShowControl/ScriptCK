#!/usr/bin/env python
'''
script_ck.py: Takes the parsed script data-structure, returns a list of
issues to be corrected.
'''

__author__ = 'bapril'
__version__ = '0.0.4'

class ScriptError(object):
    """Class to hold errors"""
    def __init__(self, page, line, error):
        self.page = page
        self.line = line
        self.error = error

    def to_str(self):
        """Render the error to a string"""
        return "ERROR: Page: %d Line: %d Error: %s" % (self.page, self.line, self.error)

class ScriptCk(object):
    """Script Consistency checK Engine Class"""
    def __init__(self, target, source):
        self.source = source
        self.target = target
        self.current_char = None
        self.drap = {}
        self.word_count = {}
        self.onstage = {}
        self.mic_open = {}
        self.act = None
        self.scene = None
        self.page = 1
        self.line = 1
        self.errors = []
        self.tag = None
        self.tag_map = {}

        self.load_tag_map()

    def update(self):
        """Run Consistency checK"""
        my_input = self.source.update()
        for tag in my_input:
            print "TAG: " + str(tag)
            if 'text' in tag.keys():
                lines = tag['text'].count('\n')
                print "Increment " + str(lines) + " lines."
                self.line += lines
            self.tag = tag
            if 'type' in self.tag.keys():
                #tag has a type:
                if self.tag['type'] == 'invalid':
                    self.errors.append(ScriptError(self.page, self.line, str(self.tag)))
                else:
                    self.check_tag()
            else:
                word_count = len(self.tag['text'].split())
                if self.current_char == 'ALL':
                    #credit all chars with these words.
                    for char in self.mic_open:
                        if self.mic_open[char] is True:
                            self.word_count[char] += word_count
                elif self.current_char != None:
                    self.word_count[self.current_char] += word_count
                else:
                    if self.tag['text'].isspace():
                        #Don't need to complain about only whitespace.
                        pass
                    else:
                        self.errors.append(ScriptError(self.page, self.line, \
                            "Lines with no active char."))

        #TODO Check for on-stage chars or open mics at end of show.
        print "Finished with Script_CK"
        for error in self.errors:
            print error.to_str()
        print "Character word count."
        for char in self.word_count:
            print "Char: %s - %d" %(char, self.word_count[char])

    def check_tag(self):
        """Route a tag to the specified checking routine"""
        if self.tag['type'] in self.tag_map.keys():
            self.tag_map[self.tag['type']]()
        else:
            self.errors.append(ScriptError(self.page, self.line, \
                "Unknown tag type: %s" % self.tag['type']))

    def load_tag_map(self):
        """Create a map that maps tags to render fucntions"""
        self.tag_map['title'] = self.nop
        self.tag_map['subtitle'] = self.nop
        self.tag_map['copyright'] = self.nop
        self.tag_map['page'] = self.check_page
        self.tag_map['author'] = self.nop
        self.tag_map['invalid'] = self.nop # Add check_invalid?
        self.tag_map['dp'] = self.check_dp
        self.tag_map['location'] = self.nop
        self.tag_map['char'] = self.check_char
        self.tag_map['enter'] = self.check_enter
        self.tag_map['exit'] = self.check_exit
        self.tag_map['exeunt'] = self.check_exeunt
        self.tag_map['sd'] = self.nop
        self.tag_map['act'] = self.check_act
        self.tag_map['scene'] = self.check_scene
        self.tag_map['mute'] = self.check_mute
        self.tag_map['unmute'] = self.check_unmute

    def check_dp(self):
        """Check a DP tag"""
        name = self.tag['name']
        # - Duplicate DP char.
        if name in self.drap.keys():
            self.errors.append(ScriptError(self.page, self.line, \
                "Duplicate DP entry for: %s" % name))
        self.drap[name] = True
        self.word_count[name] = 0
        self.onstage[name] = False
        self.mic_open[name] = False

    def check_char(self):
        """Select character speaking"""
        name = self.tag['text']
        # - Character not in DP
        if name == 'ALL':
            self.current_char = 'ALL'
        elif name in self.drap.keys():
            # - Character is already speaking
            if name != self.current_char:
                if self.mic_open[name] is True:
                    self.current_char = name
                else:
                    # - Character speaking but not on Stage or unmuted.
                    self.errors.append(ScriptError(self.page, self.line, \
                        "Character speaking without mic open: %s" % name))
                    self.current_char = None
            else:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Character already speaking %s" % name))
        else:
            self.errors.append(ScriptError(self.page, self.line, \
                "Character not in DP: %s" % name))
            self.current_char = None

    def check_mute(self):
        """Check a Mute tag"""
        name = self.tag['text']
        # - Character not in DP
        if name in self.drap.keys():
            if self.mic_open[name] is True:
                self.mic_open[name] = False
            else:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Character mutes who's already muted: %s" % name))
        else:
            self.errors.append(ScriptError(self.page, self.line, \
                "Character mutes who's not in DP: %s" % name))

    def check_unmute(self):
        """Check an unmute tag"""
        name = self.tag['text']
        # - Character not in DP
        if name in self.drap.keys():
            if self.mic_open[name] is True:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Character unmutes who's already unmuted: %s" % name))
            else:
                self.mic_open[name] = True
        else:
            self.errors.append(ScriptError(self.page, self.line, \
                "Character unmutes who's not in DP: %s" % name))

    def check_enter(self):
        """Check enter tag"""
        name = self.tag['text']
        # - Character not in DP
        if name in self.drap.keys():
            # - Character entered who is already on stage.
            if self.onstage[name] is True:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Character enters who's already on-stage: %s" % name))
            else:
                self.onstage[name] = True
                self.mic_open[name] = True
        else:
            self.errors.append(ScriptError(self.page, self.line, \
                "Character enters who's not in DP: %s" % name))

    def check_exit(self):
        """Check exit tag"""
        name = self.tag['text']
        # - Character not in DP
        if name in self.drap.keys():
            # - Character exited who is not on stage.
            if self.onstage[name] is False:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Character exits who's already off-stage: %s" % name))
            else:
                self.onstage[name] = False
                self.mic_open[name] = False
        else:
            self.errors.append(ScriptError(self.page, self.line, \
                "Character exits who's not in DP: %s" % name))

    def check_exeunt(self):
        """Check exeunt tag"""
        for name in self.mic_open:
            if self.mic_open[name] is True:
                self.mic_open[name] = False
        for name in self.onstage:
            if self.onstage[name] is True:
                self.onstage[name] = False
        self.current_char = None

    def check_page(self):
        """Check end of page tag"""
        try:
            page = int(self.tag['text']) + 1
            # - Page > last page number.
            if page > self.page:
                self.page = page
                self.line = 1
            else:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Page number unchanged or regressed %d - %d" % (page, self.page)))
        except ValueError:
            # - Scene Number not valid.
            self.errors.append(ScriptError(self.page, self.line, \
                "Page number invalid %s" % self.tag['text']))

    def check_scene(self):
        """Check new scene tag"""
        try:
            scene = int(self.tag['text'])
            # - Scene > last scene number.
            if scene > self.scene:
                self.scene = scene
                self.current_char = None
            else:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Scene number unchanged or regressed %d - %d" % (scene, self.scene)))
        except ValueError:
            # - Scene Number not valid.
            self.errors.append(ScriptError(self.page, self.line, \
                "Scene number invalid %s" % self.tag['text']))

    def check_act(self):
        """Check new act tag"""
        try:
            act = int(self.tag['text'])
            # - Act > last Act number.
            if act > self.act:
                self.current_char = None
                self.scene = None
            else:
                self.errors.append(ScriptError(self.page, self.line, \
                    "Act number unchanged or regressed %d - %d" % (act, self.act)))
        except ValueError:
            # - Scene Number not valid.
            self.errors.append(ScriptError(self.page, self.line, \
                "Act number invalid %s" % self.tag['text']))
        #TODO - Act change with Characters on stage.
        #TODO - Act change with Mics open.

    def nop(self):
        """This tag has no checks"""
        pass

#Checks
# - Tag invalid
# - Lines not attributed to a character.
