"""
Management command to seed the initial ThriftHammer blog posts.

Run this on any environment (local or production) to populate the blog:
    python manage.py seed_blog
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post, Tag


POSTS = [
    {
        'title': 'My Top 5 Warhammer Content Creators (and Why You Should Follow Them)',
        'slug': 'top-5-warhammer-content-creators',
        'excerpt': (
            'From budget-friendly podcasts to elite competitive coaching, these are the '
            'five Warhammer creators every hobbyist — casual or competitive — should know about.'
        ),
        'meta_title': 'Top 5 Warhammer Content Creators You Should Follow',
        'meta_description': (
            'Poorhammer, Goonhammer, 40k in 40 Minutes, Paul is Bad at Stuff, and Art of War — '
            'the five Warhammer creators every hobbyist should follow in 2025.'
        ),
        'tags': ['Community', 'Content Creators', 'Podcasts', 'Competitive 40K', 'Budget Tips'],
        'body': """<p>Let's be honest: Warhammer 40K has never been more popular, and the content creator scene has exploded. Between YouTube channels, podcasts, websites, and Discord servers, there's more Warhammer content than ever before.</p>

<p>The following are my top 5 Warhammer creators that I genuinely think every hobbyist should check out — regardless of whether you are a casual or a competitive player.</p>

<hr>

<h2>#1: Poorhammer Podcast &mdash; <em>"My Personal Inspiration"</em></h2>

<p>Poorhammer has a simple mission: make their community laugh. Hosts Brad and Eric have this incredible chemistry where they can discuss the most recent dataslate one minute and joke about meme armies they want to build next.</p>

<p>These guys bring an extremely positive and hilarious energy to 40K unmatched by any creator in the space. They stress fun over competition — which is something I think most of us can stand behind. Episodes like <em>"The Four Horsemen of 9th Edition"</em> are hilarious breakdowns of the most broken units in recent memory, while their <em>"Meme Lists You Should Never Build"</em> series are always straight bangers.</p>

<p>The best episodes have to be the ones focused on saving their community money. <em>"The $500 Army Challenge"</em>, <em>"Every Faction's Combat Patrol"</em>, and <em>"The Kitbashing Class"</em> were direct inspirations in creating <a href="https://thrifthammer.com">ThriftHammer.com</a>. While not every episode is my jam, there are no 40K podcasts I would put ahead of Poorhammer.</p>

<hr>

<h2>#2: Goonhammer &mdash; <em>"The Encyclopedia of Warhammer"</em></h2>
<p><strong>Format:</strong> Website (<a href="https://www.goonhammer.com" target="_blank" rel="noopener">Goonhammer.com</a>)</p>

<p>If Poorhammer is your fun friend who teaches you the game over beers, Goonhammer is the comprehensive textbook you probably need to read. Founded in 2018 by a group of former SomethingAwful forum posters, Goonhammer has become the definitive resource for the entire Games Workshop ecosystem.</p>

<p>Goonhammer's archives stretch deep and you are in for hours of content for whatever Games Workshop game you are interested in. When I started Necromunda, Goonhammer was the first site I visited. When Bloodbowl Season 3 dropped, Goonhammer team guides kept me busy for hours building rosters for each team. For Warhammer, Goonhammer is the website for all gamers covering all parts of the hobby.</p>

<p>My favourite Goonhammer article to this day remains <a href="https://www.goonhammer.com/to-all-the-armies-weve-loved-before/" target="_blank" rel="noopener">"To All the Armies We've Loved Before"</a> — a retrospective on armies let go by the panel of writers. I think many of us can sympathise, having had the experience of dropping a project or army at some point during our hobby journey. For newer players to any Warhammer-affiliated hobby, check out Goonhammer's faction and team guides — they are excellent resources for getting started.</p>

<hr>

<h2>#3: 40K in 40 Minutes (Play on Tabletop) &mdash; <em>"Battle Reports Done Right"</em></h2>

<p>Battle reports are typically a slog. Three-hour videos where you can barely see what's happening, shaky camera work, confusing board states — we've all sat through bad ones. 40K in 40 Minutes figured out the perfect formula: tight editing, clear camera angles, great production value, and — most importantly — they're actually fun to watch.</p>

<p>The Play on Tabletop crew may not be the most competitive players but there is a positive energy that sweeps through every game. Their reports move quickly and are punctuated with powerful narrative moments that leave a lasting impact. They are not the best resource for strategy or meta analysis, but they are unmatched in production quality and sheer watchability.</p>

<p>My personal favourites are always the matchups featuring Nick or channel voice JT, who bring top-notch sportsmanship and charisma to every game. A recent highlight: <a href="https://youtu.be/jQZWfOJXU2c?si=eP4xDwpJKOP13q9d" target="_blank" rel="noopener">Nick vs Space Marine Steve</a>. Always look forward to new battle reports every week.</p>

<hr>

<h2>#4: Paul is Bad at Stuff &mdash; <em>"The Most Relatable"</em></h2>

<p>Paul's channel name is <em>"Paul is Bad at Stuff"</em> — but here's the thing: Paul is actually pretty good at stuff. What makes his channel special isn't just the content, but how relatable he is to 99% of us gamers.</p>

<p>In a hobby that can sometimes take itself way too seriously, Paul is just a guy who wants to play with his Centurions. His passion for such a mid unit (sorry Paul) is infectious. Paul is a great example of how winning at any cost isn't the point — winning on your own terms, using the models you love to paint and play, is what matters.</p>

<p>My favourite series from him is <em>Hot Take Court</em>, a chaotic community-driven live stream that is pure entertainment. He is one of the most unique Warhammer content creators out there. High-end competitive players may not get much from Paul's content, but if you want refreshing and relatable hobby content, Paul is Bad at Stuff may be for you.</p>

<hr>

<h2>#5: Art of War 40K &mdash; <em>"The Competitive Deep End"</em></h2>

<p>I was on the fence about including Art of War because I don't consider myself a competitive player — but Art of War is where you go if you're <em>serious</em> about competitive 40K. Founded by some of the best players in the world, they offer premium coaching, detailed strategy content, and a subscription service (The War Room) with hundreds of hours of advanced tactical analysis.</p>

<p>Art of War assumes you already know how to play and want to master your faction. Their faction deep-dives are taught by players who've won majors with those armies. The focus is crystal clear: improving the level of competitive 40K worldwide.</p>

<p>So why do I enjoy their content (specifically the free stuff)? Honestly, I enjoy competitive 40K the same way I enjoy competitive Starcraft 2 or the NBA. It's fascinating to see what separates top players from the rest of us, and what goes through the minds of pros when army-building or executing tactics. I have no desire to reach those competitive heights myself — but it's incredibly cool to listen to the best players in the world break it all down.</p>

<p>If you're interested in competitive 40K or simply want to improve your game, Art of War is an excellent resource.</p>

<hr>

<h2>Honourable Mentions</h2>
<ul>
    <li><strong>Adeptus Ridiculous</strong> — Best Warhammer lore channel/podcast</li>
    <li><strong>Bonehead Podcast</strong> (casual Bloodbowl) &amp; <strong>Andy Davo Bloodbowl</strong> (competitive Bloodbowl)</li>
    <li><strong>Christian Von Carmian</strong> — Sisters of Battle / Genestealer Cult specialist channel</li>
    <li><strong>Miniature Game Montage</strong> — Battle reports across various miniatures games</li>
</ul>""",
    },
    {
        'title': '5 Warhammer Kit Hacks: How to Get More Minis for Your Money',
        'slug': '5-warhammer-kit-hacks-more-minis-for-your-money',
        'excerpt': (
            'Five clever kit-bashing and buying tricks to stretch your hobby budget — '
            'from hidden Kabalites in the Ravager box to the old Ork Boyz secret weapon.'
        ),
        'meta_title': '5 Warhammer Kit Hacks: Get More Minis for Less Money',
        'meta_description': (
            'Five clever kit-bashing tricks to stretch your Warhammer budget — '
            'hidden Kabalites, Necron bit buffets, endless Intercessor sprues and more.'
        ),
        'tags': ['Budget Tips', 'Kit Hacks', 'Drukhari', 'Necrons', 'Space Marines', 'Orks', 'Tyranids'],
        'body': """<p>If you've ever stared at your hobby budget and muttered, <em>"I swear these sprues used to come with more bits,"</em> you're not alone. Welcome to the thrifty side of the hobby — where saving money doesn't mean giving up your love for plastic glory.</p>

<p>Here are our top 5 kit hacks to squeeze maximum value (and fun) from your purchases.</p>

<hr>

<h2>1. The Ravager (Drukhari) — Free Kabalites for Days</h2>
<p>The Ravager isn't just a skimmer of doom — it's secretly a Kabalite Warrior value pack.</p>
<p>Ignore the instructions and take those Kabalites seated on the pirate ship and kitbash them into a squad of Kabalite Warriors. If you're super-thrifty, pair those leftovers with bits from your friends' spare elf boxes, and boom — you've got an entire extra squad's worth of Drukhari.</p>

<h2>2. The Necron Warrior Box — The Endless Bit Buffet</h2>
<p>Necrons might sleep for millennia, but this box never rests when it comes to value. You get Gauss Flayers <em>and</em> Reapers for all 10 models, meaning whichever weapon you don't use becomes future conversion gold.</p>
<p>Build one full squad with Reapers and use the spare Flayers to kitbash your old Warriors — they'll rise again, cheaper than ever. Combine that with used bits from eBay, and you'll be fielding the dreaded silver horde for a fraction of the cost.</p>

<h2>3. Space Marine Intercessors — Chapter of Endless Options</h2>
<p>Each Intercessor sprue comes loaded with so many spare arms, helmets, and purity seals you could start a small relic shop. Combine them with leftover Assault Intercessor bodies and you'll have unique veterans ready to serve the Emperor.</p>
<p>As a Grey Knights player, I've bought my fair share of Space Marine bits online — and let me tell you, those extras are worth their weight in gold.</p>

<h2>4. The Old Ork Boyz Box — Da More, Da Merrier</h2>
<p>Sometimes, new ain't betta. The old Ork Boyz kit absolutely kicks da teef outta the newer one. A single box gives you more Orky goodness for kitbashing and spreading the WAAAGH.</p>
<p>You'll find an extra Ork body and a ton of wargear options to create the customized horde of your dreams. Grab one old Boyz box and one new — combine 'em for Da Bestest Boyz Mob this side of Armageddon.</p>

<h2>5. Tyranid Warriors — The Biomorph Bonanza</h2>
<p>Every sprue in this kit includes all possible biomorph weapons — bone swords, lash whips, venom cannons, and more. Build one loadout now and save the rest for magnetizing later or customizing smaller creatures.</p>
<p>If you're starting Tyranids, this is the value kit to anchor your swarm — both financially and tactically.</p>

<hr>

<h2>Bonus: Start Collecting &amp; Combat Patrol Boxes — The Ultimate Hack</h2>
<p>Sometimes the best hack is the most obvious — buy bundled boxes strategically. Combat Patrols often offer 30–40% more models for the same price compared to individual kits.</p>
<p>If you're strapped for cash, start with the <strong>Adeptus Custodes Combat Patrol</strong> — over 700 points of gold-clad demigods ready to punch holes through the legions of Chaos and Xenos alike.</p>
<p><a href="/products/">Compare Combat Patrol prices across retailers right now on ThriftHammer</a>.</p>

<hr>

<p>Warhammer will always test both your tactical and financial skills — but with a little creativity and a sharp hobby knife, you can build beautiful armies and keep your wallet intact.</p>
<p>Whether you're kitbashing Orks or resurrecting Necrons, remember: <strong>every sprue hides a secret unit.</strong></p>""",
    },
    {
        'title': 'The 3 Best (and 3 Worst) Warhammer Video Games (That I Have Played)',
        'slug': '3-best-3-worst-warhammer-video-games',
        'excerpt': (
            'From Rogue Trader\'s grimdark storytelling to the disaster of Underhive Wars — '
            'my personal picks for the 3 best and 3 worst Warhammer video games I\'ve actually played.'
        ),
        'meta_title': 'The 3 Best (and 3 Worst) Warhammer Video Games',
        'meta_description': (
            'Rogue Trader, Space Marine, and Dawn of War make the best list — while Underhive Wars, '
            'Talisman: Horus Heresy, and Realms of Ruin get the wooden spoon.'
        ),
        'tags': ['Video Games', 'Reviews', 'Warhammer 40K', 'Age of Sigmar'],
        'body': """<p>While tabletop will always be the peak of the hobby, there's no denying that Warhammer video games have carved out their own niche among casual and hardcore fans alike. Today, players have more ways than ever to dive into the grimdark universe &mdash; but for every masterpiece that nails the tone of the 41st millennium, there's a stinker that makes you beg for the sweet mercy of Exterminatus.</p>

<p>Here are my personal picks for the 3 best and 3 worst Warhammer video games, plus a few that narrowly missed each list.</p>

<hr>

<h2>The 3 Best Warhammer Video Games</h2>

<h3>#1. Warhammer 40,000: Rogue Trader &mdash; <em>"The Emperor's Chosen CRPG"</em></h3>

<p>If you love deep stories, moral ambiguity, and tactical combat, Rogue Trader is everything you've ever wanted from a Warhammer RPG.</p>

<p>Developed by Owlcat Games (the studio behind <em>Pathfinder: Wrath of the Righteous</em>), this is the definitive Warhammer CRPG. You play as a Rogue Trader commanding a voidship, making difficult decisions while interacting with countless in-universe factions.</p>

<p>Every companion feels like a page out of a Black Library novel, yet the game remains approachable for newcomers with little lore knowledge. My favourite part? It perfectly balances being a fun video game with faithfully infusing the atmosphere and lore of 40K.</p>

<p>This is a must-buy for lore lovers, CRPG fans, or anyone who's ever wondered what it's like to command your own fleet in the Imperium.</p>

<h3>#2. Space Marine 1 &amp; 2 &mdash; <em>"The Emperor Protects&hellip; and So Do You"</em></h3>

<p>Few games truly make you feel like a Space Marine.</p>

<p>The original Space Marine was a phenomenal first attempt &mdash; fast, brutal, and gloriously over-the-top. Space Marine 2 takes that foundation and amplifies it with more scale, more violence, and even more enemies to pulp into paste.</p>

<p>It's a bombastic thrill ride that delivers exactly what you want: heavy metal carnage and righteous fury. The gameplay feels like <em>Gears of War</em> for Warhammer fans &mdash; each weapon feels satisfying to fire, every chainsword swing hits with weight, and the bloodshed is pure cinematic bliss.</p>

<p>The story does its job moving you between set pieces without ever getting in the way of the action. And with regular updates and future content planned, Space Marine 2 is only getting better.</p>

<h3>#3. Dawn of War &mdash; <em>"The OG RTS That Still Rules"</em></h3>

<p>One of Warhammer's earliest forays into video games, Dawn of War showed us what digital Warhammer could truly be.</p>

<p>I played it long before I ever touched a tabletop model &mdash; my copy came from trading a few cards with a friend. Relic's 2004 classic perfectly blended tactical base-building with brutal frontline combat. The voice lines, animations, and faction design still hit harder than most modern RTS games.</p>

<p>With expansions like <em>Dark Crusade</em> and <em>Soulstorm</em>, Dawn of War built a thriving community that's still active thanks to mods, fan patches, and the new Dawn of War Remastered.</p>

<p>The only reason it ranks #3 for me is simple: StarCraft II exists. It's hard to go back in 2026, but for many of us, Dawn of War was the gateway into both Warhammer and gaming.</p>

<hr>

<h2>Just Missed the List</h2>
<ul>
    <li><strong>Blood Bowl 2</strong> &mdash; Brutal fantasy football with dice. The best Blood Bowl video game ever made for one of GW's best specialist games.</li>
    <li><strong>Shootas, Blood &amp; Teef</strong> &mdash; Pure, chaotic fun and beautifully Orky.</li>
    <li><strong>Vermintide 2</strong> &mdash; Fantastic co-op hack-and-slash that I sadly only put a few dozen hours into before moving on.</li>
</ul>

<hr>

<h2>&#128128; The 3 Worst Warhammer Video Games</h2>

<h3>#1. Necromunda: Underhive Wars &mdash; <em>"Most Disappointing"</em></h3>

<p>Necromunda might be Warhammer's coolest setting &mdash; dark, industrial, and full of gang warfare. On paper, Underhive Wars should've been a slam dunk: a gritty, tactical skirmish game in the hive's depths.</p>

<p>Instead, what we got was a buggy, confusing mess with terrible AI, clunky mechanics, and a campaign that completely missed the tone of the tabletop game.</p>

<p>The AI is so bad it ruins single-player entirely. And with the multiplayer scene long dead, there's virtually nothing left for new players. Even at its frequent $2 sale price, Underhive Wars is a chore to play.</p>

<p>I had high hopes because Necromunda on tabletop is a blast &mdash; full of stories, betrayal, and personality. Unfortunately, this game's failure likely killed any chance of another Necromunda adaptation for years to come.</p>

<p><em>Necromunda deserves better.</em></p>

<h3>#2. Talisman: The Horus Heresy &mdash; <em>"Why Did I Play This?"</em></h3>

<p>Long story short: I played this with a friend who loves Talisman&hellip; and I learned I don't.</p>

<p>I'm a huge board gamer (<em>Terraforming Mars</em>, <em>Gaia Project</em>, <em>Wingspan</em>), so I was curious to finally try Talisman &mdash; especially with a Warhammer 40K skin. But what I got was a slow, repetitive, random slog that felt like watching paint dry on a Rhino hull.</p>

<p>To be fair, it has mostly positive reviews on Steam &mdash; fans of the original Talisman appreciate the tweaks and flavour. But if you're not already a Talisman die-hard, stay away.</p>

<h3>#3. Warhammer Age of Sigmar: Realms of Ruin &mdash; <em>"Style Over Substance"</em></h3>

<p>Realms of Ruin had promise: beautiful visuals, an ambitious RTS setup, and the chance to finally give Age of Sigmar its moment in the spotlight.</p>

<p>But it just never delivers. The gameplay is slow and shallow, the missions repetitive, and the factions lack meaningful variety. It's an RTS that fails at the fundamentals &mdash; no strategic depth, limited unit diversity, and a story so generic it feels like it was written by a servitor.</p>

<p>Worse, the game leans heavily into DLC and monetisation rather than delivering a complete experience. Even with low expectations, I was shocked by how half-baked the final product felt.</p>

<p><em>Realms of Ruin looks incredible &mdash; but plays like a tech demo.</em></p>

<hr>

<h2>Final Thoughts</h2>

<p>Warhammer video games are like the galaxy itself &mdash; a mix of glory, horror, and occasional disaster.</p>

<p>When they work (<em>Rogue Trader</em>, <em>Space Marine</em>, <em>Dawn of War</em>), they pull you deep into the 41st millennium and remind you why you love the universe. When they don't (<em>Underhive Wars</em>, <em>Realms of Ruin</em>), they make you want to offer your GPU to the Machine God in penance.</p>""",
    },
]


class Command(BaseCommand):
    """Seed initial blog posts into the database."""

    help = 'Seeds the initial ThriftHammer blog posts. Safe to re-run — skips existing slugs.'

    def handle(self, *args, **options):
        """Create tags and posts if they do not already exist."""
        created_count = 0
        skipped_count = 0

        for post_data in POSTS:
            if Post.objects.filter(slug=post_data['slug']).exists():
                self.stdout.write(f"  [skip]  {post_data['title']}")
                skipped_count += 1
                continue

            # Resolve / create tags
            tags = []
            for tag_name in post_data.get('tags', []):
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                tags.append(tag)

            post = Post.objects.create(
                title=post_data['title'],
                slug=post_data['slug'],
                excerpt=post_data['excerpt'],
                body=post_data['body'],
                status=Post.STATUS_PUBLISHED,
                published_at=timezone.now(),
                meta_title=post_data.get('meta_title', ''),
                meta_description=post_data.get('meta_description', ''),
            )
            post.tags.set(tags)

            self.stdout.write(f"  [new]   {post.title}")
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone! Created: {created_count}  |  Skipped: {skipped_count}'
            )
        )
