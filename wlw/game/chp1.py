from wlw.utils.chapter import Chapter
from wlw.utils.character import Character
import time

CHAPTER_TITLE = "False Beginnings"
CHAPTER_NUMBER = 1

class Main(Chapter):
    def __init__(self, manager, renderer):
        super().__init__(manager, renderer)
        self.title = CHAPTER_TITLE

        self.nih = self.manager.register_character(Character("Nihira Khimaris", "f", 0, True))
        self.emi = self.manager.register_character(Character("EdEn:TU9A-EMIL (Emil Khmaris)", "f", 60, hidden=True))
        self.mav = self.manager.register_character(Character("Mavrn Aenchalii", "m", 15, hidden=True))
        self.narr = self.manager.register_character(Character("Narrator", "m", 0, special=True))

    def start(self):
        self.narr.speak("Two people, two stories. One choice.", True)
        self.narr.speak("That choice is yours, Player.", True)

        while True:
            self.narr.speak("Who will you choose to follow?", True, True)

            self.renderer.set_choices([
                {"title": "Nihira", "id": "female"},
                {"title": "... [COMING SOON!]", "id": "male"}
                ])

            user = self.renderer.wait_choice()

            if user == "female":
                self.narr.unlock_speech()
                self.manager.persistent["player_route"] = "f"
                break
            else:
                self.narr.unlock_speech()
                continue

        self.narr.speak("This choice is the first of many.", True)
        self.narr.speak("Make them wisely.", True)
        self.narr.speak("...", True)

        if self.manager.persistent["player_route"] == "f":
            self.narr.speak(f"Chapter One: {self.title}", True)
            self.f_intro()

    # female 'Commander' route start
    def f_intro(self):
        self.manager.set_section(self.title, "f_intro")
        self.manager.save()

        self.nih.speak("Arcallis.")
        self.nih.speak("The New Order.")
        self.nih.speak("The Enemy.")
        time.sleep(0.5)
        self.nih.speak("Alone, these things may have been perfectly docile.")
        self.nih.speak("But together, they've brewed a chaos that destroys anything and anyone involved.")
        self.nih.speak("Our Ancestors knew this well. Yet they're the ones who brought this upon us.")
        self.nih.speak("This fact alone paints a foul picture over the cataclysmic event that brought us here.")
        time.sleep(0.3)
        self.emi.speak("...commander...")
        time.sleep(0.3)
        self.nih.speak("The Great Rebirth, they call it.")
        self.nih.speak("An eye for an eye, a universe for a universe—such is all they make it out to be.")
        self.nih.speak("Our self-proclaimed scientists claim it is an event to cherish,")
        self.nih.speak("after all, it <i>did</i> birth Arcallis from the ashes.")
        self.nih.speak("But nobody ever stops to consider where the ashes came from.")
        self.nih.speak("Or rather...")
        time.sleep(0.5)
        self.nih.speak("Whom.")
        time.sleep(1)
        self.emi.speak("..commander.")
        time.sleep(1)
        self.nih.speak("Now, all because of our collective ignorance, they've returned, like a phoenix.")
        self.nih.speak("And they are <i>anything</i> but happy.")
        self.nih.speak("First, they started burning villages.")
        self.nih.speak("Next, the planets.")
        self.nih.speak("Who knows how many more lives will be lost in this gods-forsaken war?")
        self.nih.speak("...")
        self.nih.speak("Regardless, <i>someone</i> has to fight.")
        self.nih.speak("I simply wish it di-<s>")
        self.emi.speak("Commander!")

        self.nih.speak("A sharp voice pierces into my thoughts, yanking me out of my former dream state.", True)
        self.nih.speak("My eyes shoot open as I rise with a gasp, the sudden awakening taking me by surprise.", True)
        self.nih.speak("H-huh?! Wha-...")
        # self.narr.speak("After only a moment, I connect the voice with the person staring angrily at me from across the table,")
        # self.narr.speak("but as I open my mouth to protest, she abruptly cuts me off:")
        self.emi.speak("Finally, you're awake!")
        self.nih.speak("I recognize her judgemental glare almost immediately as she continues to scold me:", True)
        self.emi.speak("The fact that you haven't been caught asleep by the enemy is <i>astounding.</i>")
        self.nih.speak("Unit EdEn:TU9A-EMIL, designation: 'Emil Khmaris'. Not only my first officer, but apparently my new alarm clock...", True)
        self.emi.hidden = False
        self.nih.speak("She's dressed in her military attire, with her dark, purplish hair still cut well above her shoulders.", True)
        self.nih.speak("Her EdEn System, undisguised and in its default cuboid form, has also moved, now hanging beside her waist, still shimmering lightly in the dark.", True)
        self.nih.speak("Knowing her, she had likely taken a visit to the battle simulator and hadn't bothered to change.", True)
        self.nih.speak("I'm not sure just how long she's been here watching me though, but judging by the intensity of her iconic glare, probably too long.", True)
        time.sleep(0.2)
        self.nih.speak("She continues:", True)
        self.emi.speak("Commander, are you <i>sure</i> you received enough sleep last night? This is the third time today you've dozed off.")

        self.narr.speak("I take a moment to recall what exactly I had been doing last night, before replying:", True, True)

        self.renderer.set_choices([
            {"title": "Make up an excuse", "id": "lie"},
            {"title": "Just tell her what happened", "id": "tell"}
        ])

        user = self.renderer.wait_choice()

        self.narr.unlock_speech()

        if user == "lie":
            self.manager.persistent["player_emi_dozed-off_lie"] = True

            self.nih.speak("Can you blame me? We've been drifting through the void for weeks now.")
            self.nih.speak("Seeing the same black nothingness all day everyday gets boring quick.")

            self.nih.speak("She remains silent for a moment, the judging look plastered on her face only growing in intensity.", True)
            self.emi.speak("...<w=2>We're moving at speeds that render that argument irrelevant, Commander.")
            self.nih.speak("She pauses to watch my reaction, however, I manage to keep a steady face and she goes on:", True)
            self.emi.speak("Judging by the mess of papers on your desk, you were up late reading over the reports again, weren't you?")
            self.nih.speak("I let out a defeated sigh.", True)
            self.nih.speak("Alright, alright. Yes, I was. But it's only because the New Order won't stop sending them!")
            self.nih.speak("At this rate, I'll be drowning in reports even <i>if</i> I stay up reading all these things...")
        elif user == "tell":
            self.manager.persistent["player_emi_dozed-off_lie"] = False

            self.nih.speak("I was up late reading all the reports from the New Order that the chief keeps sending me.")
            self.nih.speak("I gesture to the two stacks of paper on my desk. The larger one, of course, being the unread reports.", True)
            self.nih.speak("With a sigh, I continue:", True)
            self.nih.speak("If I don't read them all now, I'll likely be drowning in reports by next week... They just can't give me a break.")

        self.nih.speak("Emil's expression softens.", True)
        self.emi.speak("I could always assist with the paperwork, Commander. Staying up late like that is going to affect your performance.")

        self.nih.speak("I shake my head, standing up.", True)
        self.nih.speak("As much as I'd appreciate help from an Analytical Unit, that wouldn't be a good idea.")
        self.nih.speak("The chief would have a field day with me if he found out I was offloading my work.")
        self.nih.speak("Besides, it isn't.<w=0.3>.<w=0.3>.<w=0.5> that bad.")
        self.nih.speak("Emil doesn't seem to believe me, as she promptly picks up one of the reports and studies it.", True)
        self.nih.speak("Her eyes rapidly dart around, processing the text on the report faster than any average Arcallen could as I simply stand, watching.", True)
        self.nih.speak("After reading the report fully, she looks back up at me.", True)
        self.emi.speak("I don't understand how this involves you, Commander.")
        self.nih.speak("It doesn't... At least, not directly.")
        self.nih.speak("With just about three fourths of our forces being deployed, <i>somebody</i> has to do the paperwork.")
        self.nih.speak("It just so happens we're the quickest and most often available.")
        self.emi.speak("Well, I suppose they aren't incorrect...")
        self.nih.speak("Emil places the report back down onto the pile.", True)
        self.emi.speak("But even if they are, you won't be any good in battle if you're asleep, Commander.")
        self.nih.speak("What do you suppose I do, then? I can't just <i>not</i> do the work.")
        self.emi.speak("I will contact the higher ups and get them to reassign what I can. This is an unacceptable amount of reports for one person to read.")
        self.nih.speak("I let out a short laugh, unconvinced even she could get the higher ups to budge.", True)
        self.nih.speak("If you can do that, I'll buy you whatever you want next time we get to a shopping district.")
        self.nih.speak("The corners of her mouth lift ever so slightly upon hearing this as she replies:", True)
        self.emi.speak("I will make note of that, Commander. I hope you live up to your promise.")
        self.nih.speak("I smile, giving Emil a light punch on the shoulder before approaching the door to our ship's halls.", True)
        self.nih.speak("And I hope you can convince <i>somebody</i> up there that you're right. I need my beauty sleep!")
        self.emi.speak("You seem to be getting plenty of that, Commander.")
        self.nih.speak("I stop before the door and glance back at Emil.", True)
        self.nih.speak("If you needed sleep, you'd understand. Trust me.")
        self.emi.speak("Judging by your current sleep records, likely not. You seem to enjoy sleeping considerably more than the average person.")
        self.nih.speak("I roll my eyes and open the door, only briefly questioning the fact that she apparently tracks my sleeping habits.", True)
        self.nih.speak("Come on, let's check up on the others.")

        self.f_s1()

    def f_s1(self):
        self.manager.set_section(self.title, "f_s1")
        self.manager.save()

        self.narr.speak("In the hallway:", True)
        self.nih.speak("Emil walks beside me, matching my pace as we make our way down the long hall to the crew's quarters.", True)
        self.nih.speak("She seems to be thinking about something, judging by the blank look on her face and her eyes staring off into the distance.", True)
        self.nih.speak("By now, with the ship's lights at full brightness, the halls are rather empty aside from us two. Most of the crew are likely at their stations.", True)
        self.nih.speak("The awkward silence that fills the halls drags on for only a moment before I ask:", True)
        self.nih.speak("How close are we? We've been moving at maximum speed for quite a while now.")
        self.nih.speak("The question snaps Emil out of whatever robotic trance she was in and she swiftly responds:", True)
        self.emi.speak("Navigation reports we have traveled 93% of the current route. With our current heading, we should arrive by the end of the week.")
        self.nih.speak("If the battle is still going by then...", True)
        self.nih.speak("Understood. How's our Blink Drive doing?")
        self.nih.speak("This time, Emil takes a moment to respond.", True)
        self.emi.speak("Engineering still has no estimate, but they claim the repairs are going smoothly.")
        self.nih.speak("I sigh.", True)
        self.nih.speak("They claimed that last month...")
        self.emi.speak("It is delicate technology, Commander. These repairs take time.")
        self.nih.speak("I know. But an Arcallen ship without its Blink Drive is like a bird without its wings. I don't like the thought of not having an escape route.")
        self.nih.speak("Emil gives me a reassuring look.", True)
        self.emi.speak("I'm sure we'll be fine, Commander. We still have our long range comms if we require backup.")
        self.nih.speak("That's if their flimsy Blink Drives are doing any better than ours.")
        self.nih.speak("I hear a light chuckle from Emil.", True)
        self.emi.speak("I'm sure they are, Commander.")

        self.nih.speak("Our idle chatter continues as we make our way through the halls, eventually leading to the Recreational Area.", True)
        self.nih.speak("Emil looks at me quizically, apparently only now realizing our destination.", True)
        self.emi.speak("Recreation?")
        self.nih.speak("Of course. I imagine most of our fighting crew is here, since we're still so far away from our destination.")
        self.nih.speak("Emil takes a moment to reply, her eyes narrowing briefly as she mulls something over.", True)
        self.emi.speak("Understood, Commander.")

        self.nih.speak("The Recreational Area is rather large, containing all sorts of activities to keep morale high and crew entertained.", True)
        self.nih.speak("Not only are their various card and board games spread out on the room's many tables, in a dedicated corner lay several odd consoles.", True)
        self.nih.speak("On the opposite corner (and most of the wall parallel to us) are several seats stood before a counter, serving as a bar of sorts, although no alcohol would be served at a time like this.", True)
        self.nih.speak("Emil must have noticed me eying one of the consoles, because she gives me a light shove before whispering:", True)
        self.emi.speak("Go ahead.")
        self.nih.speak("I shake my head, turning away from the gorgeous array of potential and face Emil.", True)
        self.nih.speak("I can resist.")
        self.nih.speak("This statement is only half true. The expansive world of battle-sims is one that pains me to ignore after not being able to fight properly for so long.", True)
        self.emi.speak("I highly doubt that, Commander. However, I will entertain your delusions for as long as you choose to indulge in them.")
        self.nih.speak("I chuckle nervously at her odd response.", True)
        self.nih.speak("Cut me some slack... I miss the thrill of fighting.")
        self.nih.speak("Emil's eyes lock onto a group of people playing some sort of card game that had recently started, immediately taking her attention from me. She responds absentmindedly.", True)
        self.emi.speak("We could always switch roles, Commander...")
        self.nih.speak("I reply with a huff.", True)
        self.nih.speak("And shatter my hip <i>again?</i> No thank you. Unless you feel like falling back a smidge, I don't think I would survive.")
        self.nih.speak("Besides, you've become a better fighter than I ever was.")

        self.nih.speak("Emil does not respond, her focus now entirely on the game of cards. Her eyes follow the players hands as each one has their turn, and I imagine she's keeping track.", True)
        self.nih.speak("I am already well aware of her love for card games. Being an Analytical Unit, her skills can fully shine when deciphering the looks of other players depending on their hand.", True)
        self.nih.speak("It is because of those skills that I have not won a single card game against her, and likely won't ever for the foreseeable future.", True)
        self.nih.speak("With how intently she's staring at the ongoing game, I imagine she wants to join, and badly.", True)

        self.nih.speak("Before I can bring it up to her, however, a somewhat familiar face enters my view.", True)
        self.nih.speak("As he approaches, he loudly begins:", True)
        self.mav.speak("Well, well, well! If it isn't the Commander herself!")
        self.nih.speak("Mavrn Aenchalii. Our team's resident doctor, about half of the entire medical team, and also one of my biggest headaches.", True)
        self.mav.hidden = False
        self.nih.speak("Like Emil, Mavrn is dressed in his military attire, though his is donned with more medical related items and a special type of pin on his collar.", True)
        self.nih.speak("Before I have the chance to respond to his over-dramatic entrance, he continues:", True)

        self.mav.speak("Shocked to see you here, Commander! I thought you'd still be snoozing in that office of yours.")

        if self.manager.persistent["player_emi_dozed-off_lie"]: # player lied to Emil about dozing off, why should she defend them?
            self.nih.speak("Emil glances at Mavrn as if to say something, but remains silent.", True)
            self.nih.speak("You know how much paperwork they give me, Mavrn. I'm not just dozing off because I feel like it.")
            self.nih.speak("As much as I would like to stay up all night doing something <i>fun</i>, that isn't exactly in my job description.")

            self.nih.speak("Mavrn raises a brow, clearly not believing me.", True)
            self.mav.speak("Is that right?")
            self.nih.speak("I simply nod, folding my arms over my chest in defiance.", True)
            self.f_s2()
        else:
            self.f_s1_mavrn()

    def f_s1_mavrn(self):
        """
        Mavrn starts bullying Emil lul.
        """
        self.manager.set_section(CHAPTER_TITLE, "f_s1_mavrn")
        self.manager.save()

        self.nih.speak("Emil's focus is broken away from the ongoing card game and she turns her attention to Mavrn, her gaze narrowing into a glare.", True)
        self.emi.speak("The Commander was up late reading reports, Doctor. You shouldn't be making such baseless assumptions.")
        self.nih.speak("Mavrn's stare remains fixated on me, as if he hadn't heard Emil's words at all.", True)

        self.mav.speak("As our Commander, I feel your efforts would be better utilized somewhere else than the dreamland.")
        self.nih.speak("I scoff.", True)
        self.nih.speak("Yeah? Well, if you'd like to do your own paperwork for the medical reports, maybe I'd have less work to do and could get a good night's sleep.")
        self.mav.speak("Fleet wide death reports aren't my job, Commander. Only injuries and deaths of people under my care.")
        self.nih.speak("Then I would <i>appreciate</i> it if you would stop pestering me about my sleeping habits. Emil does that enough for me already.")
        self.mav.speak("So your battle robot's your alarm clock now? What an interesting turn of events.")

        self.nih.speak("Emil's expression only hardens.", True)
        self.emi.speak("I am not just a 'battle robot', Doctor. I am perfectly capable of preforming more than just one set of tasks.")
        self.mav.speak("Oh, I'm <i>sure</i>. That artifical brain of yours must be <i>whirring</i> away at the thought of it.")

        self.nih.speak("The tension between the two is clearly getting exponentially worse.", True, True)

        self.renderer.set_choices([
            {"title": "Pull the 'role' card and stop their arguing.", "id": "defend"},
            {"title": "Let them resolve the issue themselves.", "id": "silent"}
        ])

        user = self.renderer.wait_choice()
        self.nih.unlock_speech()

        if user == "defend":
            self.f_s1_mavrn_defend()
        elif user == "silent":
            self.f_s1_mavrn_silent()


    def f_s1_mavrn_defend(self):
        """
        Defend Emil.
        """
        self.manager.set_section(CHAPTER_TITLE, "f_s1_mavrn_defend")
        self.manager.save()

        self.nih.speak("")

    def f_s1_mavrn_silent(self):
        """
        Stay silent.
        """
        ...

    def f_s2(self):
        self.manager.set_section(CHAPTER_TITLE, "f_s2")
        self.manager.save()
