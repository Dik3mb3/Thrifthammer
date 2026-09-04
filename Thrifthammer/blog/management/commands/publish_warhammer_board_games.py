"""
Management command: publish_warhammer_board_games

Creates 'Top 5 Warhammer Board Games Worth Your Time & Money' blog post.
Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_warhammer_board_games
    python manage.py publish_warhammer_board_games --force
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'best-warhammer-board-games'
SITE_URL = 'https://thrifthammer.com'


def _static(path):
    return f'{SITE_URL}{staticfiles_storage.url(path)}'


BODY = """\
<style>.wbg-strike{{text-decoration:line-through;}}</style>
<p><a href="https://thrifthammer.com/products/?category=warhammer-40000&amp;faction=custodes&amp;sort=discount">Warhammer 40K</a> and <a href="https://thrifthammer.com/products/?category=age-of-sigmar&amp;sort=discount">Age of Sigmar</a> are the titans of the miniature market, yet the Warhammer universe has been spun off across different media types. Warhammer video games are just as popular (if not more) than the miniatures game and Warhammer novels have their own cult following. Heck even the most popular TCG Magic: The Gathering has done a Warhammer set. The one area Warhammer has had a checkered past is board games. The Warhammer IP has produced some really great board games, but in total honesty a majority of them are just mediocre and raided for bits and models for the miniatures game.</p>

<p>In a previous post I talked about some of the <a href="https://thrifthammer.com/blog/cheap-warhammer-miniatures-target/">exclusive board games sold at Target</a> that are a treasure trove for cheap miniatures to add to your established 40K armies.</p>

<p>However, there are Warhammer board games that are excellent for the game itself not just for the miniatures inside. As someone who loves board games and the Warhammer universe, I want to spotlight some amazing Warhammer board games that deserve to be played more often whether you are a hardcore competitive 40K player or someone who runs casual board game nights.</p>

<h2>What Games Missed the Cut</h2>

<p>There are a lot of Warhammer board games especially if you count IP versions of popular games such as Munchkin, Talisman, Monopoly, etc. These will not be included mainly because they are rethemes of an established board game and partly because they aren't the best games available to gamers.</p>

<p>I also avoided smaller scale skirmish games like <a href="https://thrifthammer.com/products/?category=kill-team&amp;sort=discount">Kill Team</a> and <a href="https://thrifthammer.com/products/?category=warcry&amp;sort=discount">Warcry</a>. Also, if I haven't played the game and can't endorse them, I excluded it regardless of how positively it has been received. Finally, I did not consider things like miniature value in the box for this ranking. Warhammer games that provide phenomenal miniatures at below GW prices like Dawn of War or the new Tacticus release were excluded. These games, while not terrible are more known for the miniatures inside them than the game they come with.</p>

<h2>The Top 5</h2>

<p>I ranked these solely on how I enjoy the game and how passionately I would recommend this to someone who plays the miniature games and those who play solely board games.</p>

<p>For the breakdown of each game, I heavily leaned on BoardGameGeek the premier site for hobby board gaming for stats, making some slight adjustments.</p>

<h2>1. <a href="https://boardgamegeek.com/boardgame/457587/blood-bowl-third-season-edition" target="_blank" rel="noopener noreferrer">Blood Bowl</a></h2>

<img src="{blood_bowl_img}" alt="Warhammer Blood Bowl Third Season Edition box art" width="831" height="600" loading="lazy">

<table>
  <tbody>
    <tr><th>Players</th><td>2</td></tr>
    <tr><th>Play Time</th><td>60-180 minutes</td></tr>
    <tr><th>Complexity</th><td>4/5</td></tr>
    <tr><th>Release Year</th><td>1986 (original release) 2025 (current edition)</td></tr>
    <tr><th>My Rating</th><td>[10/10] Best <span class="wbg-strike">Miniatures Games</span> Board Game of All Time!</td></tr>
  </tbody>
</table>

<h3>Wait, Isn't Blood Bowl a Miniature Game?</h3>

<p>Is <a href="https://thrifthammer.com/products/?category=blood-bowl&amp;sort=discount">Blood Bowl</a> a board game or miniatures game? In my opinion it's a miniatures game, however the internet disagrees with me and most consider it a board game. Is it because it's played on a board and has no measuring? Anyway, it doesn't matter because I love Blood Bowl and if this lets me talk about it, I will side with the internet. In my humble opinion Blood Bowl is the greatest Games Workshop Game ever created (sorry 40K and AoS).</p>

<h3>What Is Blood Bowl?</h3>

<p>Blood Bowl is fantasy football with players taking over factions of orcs, elves, dwarfs, undead, vampires and other Warhammer fantasy races. It's a mix of American football and Rugby with each faction having their own playstyle. Two teams of 11 players take turns moving players around a pitch, blocking opponents using custom block dice, handling and passing the ball through D6 checks, and trying to get it into the end zone to score touchdowns. You play two halves of 8 turns attempting to score on your opponent while simultaneously killing and injuring their players to gain a player advantage as the game progresses. Certain teams excel at the scoring portion of the game (Those Darn Elves and <a href="https://thrifthammer.com/products/?category=age-of-sigmar&amp;faction=skaven&amp;sort=discount">Skaven</a>), while some want to inflict as much damage as possible to get a numbers advantage.</p>

<p>Beyond a single one-off match, Blood Bowl supports league play which can serve as either a competitive and/or narrative experience with players gaining experience and unlocking new skills giving your team its own narrative arc. Blood Bowl has also expanded to have variant game modes like Sevens (quicker games), Dungeon Bowl (Blood Bowl in narrow Dungeons), and Gutter Bowl (Sevens, but better in my opinion).</p>

<h3>Why Should You Play Blood Bowl?</h3>

<ul>
  <li>Leagues build narrative. If you are a narrative player nothing beats your Troll eating their Goblin teammate or an unexpected turn 16 touchdown to win a game.</li>
  <li>A lot of content to keep you entertained for years. 30 Games Workshop official teams (31 total teams) to play with and multiple game variant available (including Blitz Bowl the smaller cousin of Blood Bowl). If you get tired of that there are a few dozen community made teams to try out.</li>
  <li>Competitive scene is amazing! Some of the nicest and most friendly players you will ever meet. Tournaments are held across the world.</li>
  <li>A very relaxed, inclusive community. 3D printed models are not just accepted but welcomed by the community. Creativity and sportsmanship are celebrated at events as much as winning.</li>
</ul>

<h3>Where Can I Find It?</h3>

<p>Great news you can find it everywhere! Blood Bowl has had a renaissance over the last decade after being abandoned by Games Workshop for years. The current edition just launched last year so this is a great time to join in the fun as new and existing players adjust to the new edition.</p>

<p>My recommendation for a new player depends on their situation. If you plan to join an established league buy a box of your favorite team, get some custom Blood Bowl block dice, and D6s and call it a day. Your local community should have pitches you can play on and you can always proxy Star Players or anything else you need. If you plan on playing with friends and you are starting from scratch picking up the Starter Box may be useful as it comes with two teams and all the stuff you need to play. If you don't like the two teams in the box or have a limited budget 3D print your own and find/create a pitch for cheap online.</p>

<h2>2. <a href="https://boardgamegeek.com/boardgame/90137/blood-bowl-team-manager-the-card-game" target="_blank" rel="noopener noreferrer">Blood Bowl: Team Manager</a></h2>

<img src="{team_manager_img}" alt="Blood Bowl Team Manager: The Card Game box art" width="605" height="600" loading="lazy">

<table>
  <tbody>
    <tr><th>Players</th><td>2-4 (best at 4)</td></tr>
    <tr><th>Play Time</th><td>60-120 minutes</td></tr>
    <tr><th>Complexity</th><td>2/5</td></tr>
    <tr><th>Release Year</th><td>2011</td></tr>
    <tr><th>My Rating</th><td>[8/10]</td></tr>
  </tbody>
</table>

<h3>What Is Blood Bowl: Team Manager?</h3>

<p>Déjà vu Blood Bowl again? Not exactly! While Blood Bowl: Team Manager is rooted in the Blood Bowl universe it focuses on managing the team rather than playing with the individual players.</p>

<p>Team Manager is a standalone card game in which players manage teams over a five-week season (5 rounds), competing in tournaments for prizes, obtaining star players, and vying for the top spot by end of game. You place cards from your deck in various tournaments being held that week allocating your cards across these different tournaments strategically. Each player's deck is unique focus on a particular team (for example Dwarves) having a playstyle similar to how the team operates in classic Blood Bowl. These cards depict players from their corresponding Blood Bowl team each having unique special abilities that can swing who wins a particular round.</p>

<h3>Why Should You Play Blood Bowl Team Manager?</h3>

<ul>
  <li>If you play Blood Bowl already you will love the humor, absurdity of the game and appreciate the nods to the original game while not being a direct copycat.</li>
  <li>Pretty fast after a few plays. It takes our group around 75 to 90 minutes for 4 player games which is half the time of an average Blood Bowl game. A fast way to get the Blood Bowl flavor we all love.</li>
  <li>A ton of content in box. You have multiple teams (various playstyles) plus there is an expansion that comes with more teams if you get bored.</li>
</ul>

<h3>Where Can I Find it?</h3>

<p>Sadly, Blood Bowl Team Manager is out of print, but you can still find the game on eBay for $50 to $60. While not cheap the price is reasonable for an out of print IP-based game. The expansion, however, is rarer and can increase the overall price to over $150. The expansion is not required to have fun but from my experience it does add more content to the game giving it more replay ability. As the Bonehead Podcast says, "More Blood Bowl is More Better".</p>

<p>There is even a <a href="https://boardgamegeek.com/thread/2614642/legendary-edition-final-release-except-potential-t" target="_blank" rel="noopener noreferrer">fan expansion</a> you can print out at home, adding more teams and content to an already great game. If you are even remotely interested and can find a decently priced copy Blood Bowl Team Manager is an underrated gem worth owning. Even if you hate it since it's out of print and not likely to be reprinted the sell you should be able to sell it for the same price you bought it for (or even more).</p>

<h2>3. <a href="https://boardgamegeek.com/boardgame/43111/chaos-in-the-old-world" target="_blank" rel="noopener noreferrer">Chaos in the Old World</a></h2>

<img src="{chaos_old_world_img}" alt="Chaos in the Old World board game box art" width="692" height="600" loading="lazy">

<table>
  <tbody>
    <tr><th>Players</th><td>3-4 (best at 4)</td></tr>
    <tr><th>Play Time</th><td>60-120 minutes</td></tr>
    <tr><th>Complexity</th><td>3/5</td></tr>
    <tr><th>Release Year</th><td>2009</td></tr>
    <tr><th>My Rating</th><td>[8/10]</td></tr>
  </tbody>
</table>

<h3>What Is Chaos in the Old World?</h3>

<p>Chaos in the Old World puts each player in control of one of the four Chaos Powers (<a href="https://thrifthammer.com/products/?category=age-of-sigmar&amp;faction=blades-of-khorne&amp;sort=discount">Khorne</a>, <a href="https://thrifthammer.com/products/?category=age-of-sigmar&amp;faction=maggotkin-of-nurgle&amp;sort=discount">Nurgle</a>, <a href="https://thrifthammer.com/products/?category=age-of-sigmar&amp;faction=disciples-of-tzeentch&amp;sort=discount">Tzeentch</a>, or <a href="https://thrifthammer.com/products/?category=age-of-sigmar&amp;faction=hedonites-of-slaanesh&amp;sort=discount">Slaanesh</a>) as they compete to corrupt and ultimately destroy the Old World before the mortal races can stop them. It's a race and a fight at the same time as each player uses their unique powers to fight for control of regions across the board. Each god is totally unique on how they approach the game each with their own unique deck of card, abilities, and paths to victory.</p>

<h3>Brief Rules Explanation</h3>

<p>Each player is trying to fill their god's unique victory dial, or hit their specific win condition, before the others do, using a shared pool of regions on the Old World map as the board.</p>

<p>A typical turn involves choosing where to deploy your god's followers, using upgrade cards to strengthen your abilities, and either building up corruption in a region or triggering direct conflict with your opponents. Because every god's dial fills differently, players are playing asymmetrically from each other utilizing different strategies to stay ahead while keeping an eye on other players to prevent them from reaching their own victory condition.</p>

<h3>What Makes Chaos in the Old World So Good?</h3>

<ul>
  <li>The asymmetry is top tier. Each god plays a different game, which mirrors how each god works in the Warhammer universe.</li>
  <li>Strong Player interaction. You're constantly weighing whether to attack, corrupt, or simply race ahead. You can't ignore the table when you play this game, you must always keep an eye on your opponents.</li>
  <li>Strong theme integration. This doesn't feel like a generic Ameritrash board game wearing a licensed Warhammer skin. Designer Eric Lang did a great job in combining bog-standard area-majority mechanics with the craziness of the Chaos Gods.</li>
</ul>

<h3>Where Can I Find It?</h3>

<p>It's widely available, for the low price of $150+. As my sarcasm suggests like Blood Bowl Team Manager, Chaos in the Old World is out of print yet is far more expensive. As the product of popular board game designer Eric Lang alongside very positive reception secondhand prices have remained high. If you want the expansion, The Horned Rat, expect to pay nearly $400 just for this expansion! I can't in good faith recommend you buying even the core game for $150. As an analog experience the miniatures are a bit below par and the look of the game is okay but not worth a $150 price tag. Seek this out if you can find it for under $100 and you have the right group to play this with. This is a 4-player game (3 player is underwhelming) that requires repeat plays to get the most out of. If this is you please be patient and grab a copy when you see the right price.</p>

<h2>4. <a href="https://boardgamegeek.com/boardgame/175155/forbidden-stars" target="_blank" rel="noopener noreferrer">Forbidden Stars</a></h2>

<img src="{forbidden_stars_img}" alt="Forbidden Stars board game box art" width="246" height="246" loading="lazy">

<table>
  <tbody>
    <tr><th>Players</th><td>2-4 (best at 3)</td></tr>
    <tr><th>Play Time</th><td>120-240 minutes</td></tr>
    <tr><th>Complexity</th><td>4/5</td></tr>
    <tr><th>Release Year</th><td>2015</td></tr>
    <tr><th>My Rating</th><td>[7/10]</td></tr>
  </tbody>
</table>

<h3>Be Warned</h3>

<p>I have only played Forbidden Stars once during a convention, so I am not well-versed in the deep strategy and my memory is a bit hazy. Take my review with a grain of salt, but the experience was great. While my rating may seem low (we will talk about that) this was so memorable that even today I am still looking for someone who owns a copy to play another game. With more plays and a deeper understanding of the mechanics and more plays this game could rocket higher up the list.</p>

<h3>What Is Forbidden Stars?</h3>

<p>Forbidden Stars pits four Warhammer 40K factions <a href="https://thrifthammer.com/products/?category=warhammer-40000&amp;faction=space-marines&amp;sort=discount">Space Marines</a>, <a href="https://thrifthammer.com/products/?category=warhammer-40000&amp;faction=chaos-space-marines&amp;sort=discount">Chaos Space Marines</a>, <a href="https://thrifthammer.com/products/?category=warhammer-40000&amp;faction=aeldari&amp;sort=discount">Eldar</a>, and <a href="https://thrifthammer.com/products/?category=warhammer-40000&amp;faction=orks&amp;sort=discount">Orks</a> against each other in a war for control of the fracturing Herakon Cluster. Players build fleets and armies, fight for territory, and race to complete objectives before their opponents. Players place 4 tokens on different sectors of the map that let them either take resources from the planet, purchase cards, deploy units, or move units across the map. The hidden orders mechanic and card and dice driven combat has shades of classic Warhammer 40K tactics with modern board game mechanics. The game's complexity is pretty insane and as a 4x game (explore, expand, exploit, and exterminate) you will be forced to interact with players at some point during the game.</p>

<h3>What Makes Forbidden Stars So Good?</h3>

<ul>
  <li>Complexity done well. Too much complexity can often be a bad thing, but in Forbidden Stars the complexity provides fertile ground for different tactics across games and factions.</li>
  <li>A true 4x game. Most 4x games are often 3x games sacrificing one portion of the game experience in order to speed up playtime or improve balance. In Forbidden Stars each of the 4x's is important to winning and ignoring portions of the mechanics is a guarantee lose.</li>
  <li>Warhammer 40k theme shines. Honestly, this is most thematic epic scale 40K experience (aside from miniatures game) available. If you love 40K but don't like the miniature portion this game is everything you need.</li>
</ul>

<h3>Issues With the Game</h3>

<ul>
  <li>Never play a 4p. This is a 2p - 3p game. A 3p game is often quoted at around 3 hours in forums. My initial play was a 4p, while fun it took 4.5 hours to play not including teach.</li>
  <li>AP (analysis paralysis) Prone players stay away. If you look for optimal moves or take long turns this game will exacerbate the issue and make the game experience longer and painful for people at that table.</li>
  <li>Rulebook is not the best, teaching &amp; learning this game can be tough. Hard to see this getting played during a casual game night or with newer players.</li>
</ul>

<h3>Where Can I Find It?</h3>

<p>I have good news and bad news. Forbidden Stars is being reprinted as Old Ones Origins a Cthulhu/eldritch reimplementation of the classic game. If you love the Warhammer theme I am sorry to say Forbidden Stars is out of print and is being routinely sold on eBay for $200 to $300. If you are interested in the mechanics of the game and don't care about the theme Old Ones Origins will certainly be cheaper when it releases and will have updated rules. For Warhammer fans $200 to $300 may be tough to stomach, but if you're truly interested there is enough game here to last you a lifetime. As an analog experience I enjoyed the miniatures and artwork when I played and if this is your grail game I won't blame anyone who shells out the money to get it. I don't expect this will ever be reprinted with the Warhammer theme again, so your decision is whether the Cthulhu theme is a good enough replacement or not.</p>

<h2>5. <a href="https://boardgamegeek.com/boardgame/337397/warhammer-underworlds-two-player-starter-set" target="_blank" rel="noopener noreferrer">Warhammer Underworlds</a></h2>

<img src="{underworlds_img}" alt="Warhammer Underworlds Two-Player Starter Set box art" width="444" height="600" loading="lazy">

<table>
  <tbody>
    <tr><th>Players</th><td>2</td></tr>
    <tr><th>Play Time</th><td>30 minutes</td></tr>
    <tr><th>Complexity</th><td>Varies on Warband</td></tr>
    <tr><th>Release Year</th><td>2017</td></tr>
    <tr><th>My Rating</th><td>[1st Edition 8/10, 2nd Edition 6/10]</td></tr>
  </tbody>
</table>

<h3>Is Warhammer Underworlds Actually a Board Game?</h3>

<p>Unlike Blood Bowl I 100% side with the belief that Underworlds is a board game. While the game uses miniatures as game pieces the game has all the hallmarks of a board game. The miniatures mean absolutely nothing in terms of game mechanics. You can replace them with in-game standees and gameplay would stay the same.</p>

<h3>What Is Warhammer Underworlds?</h3>

<p>Two players each bring a warband which is a small roster of characters, usually somewhere between 3 to 9 models onto a game board divided into hexes. Games play out over 3 rounds using a deck building system. Each player builds a deck of objective, gambit, and upgrade cards before the game, playing card as they activate their models moving them, attacking rival pieces, and completing objective cards.</p>

<p>Combat is resolved with custom dice that trigger success or failures depending on the unit's specialized card. You can win by completing objective cards even if your warband takes causalities. Each Warband plays differently some scoring more efficiently via movement shenanigans, others scoring via controlling areas of the board, and others killing rival pieces (most do a mix of all three).</p>

<h3>Why Different Ratings for Each Edition?</h3>

<p>Warhammer Underworlds 1st edition reminded me of Blood Bowl when I played it. It had unique factions each with unique flavor and playstyle that made casual games fun while having a strong competitive foundation allowing for skill expression through deck building. While I never made it past a few local tournaments, the game was easy to get into yet had enough depth that made it interesting and fun to get better at.</p>

<p>Underworlds 2nd edition really quashed my deep interest in the game. Warbands have become more generic over time (to improve balance) having less unique abilities and most Warbands utilize the same top-tier generic decks rather than the more unique 1st edition decks each warband came with. The game also feels longer than 1st edition, taking 10 to 15 min on average more (in my experience), which hurts the best of 3 format I enjoyed playing locally. I also did not enjoy the addition of catch-up mechanics of 2nd edition since being up 1 or 2 points often is a detriment than a positive with your opponent often snowballing as the underdog. Games Workshop has also slowed down the release schedule, new releases have disappointed, and balance patches have been far too slow. While at its core Underworlds remains the same game, 2nd edition changes in my opinion have been negative overall. But the 1st edition was so much fun, and 2nd edition has the potential of a comeback so I wanted to include it on the list!</p>

<h3>What Makes Warhammer Underworlds So Good (1st Edition)?</h3>

<ul>
  <li>Tactical decision-making is dense for the time investment. Every card and every activation matter.</li>
  <li>Warbands are unique in look and gameplay. Warbands use different keywords that trigger off their unique cards. Add in deck building portion you can create your own synergies keeping game play fresh over time.</li>
  <li>Low barrier to entry. A typical Warband of 5-6 models is easy to build and paint in a few days while game rules are easy to grasp. Pick up a box and then play is totally possible in Underworlds.</li>
</ul>

<h3>How to Get Into Warhammer Underworlds?</h3>

<p>You can find Warhammer Underworlds pretty easily. Games Workshop has continued to release and rerelease factions alongside new card sets. If you plan on starting with 2nd edition there are combo boxes for $80 which bring 4 warbands. Split this with a friend you got yourself 2 warbands to paint and play for $40. This is by far the best way to start today. In terms of cards it gets tricky. The best cards are often found across different releases so building the most optimal deck can get pricey. I would ignore this as a new player buying 1 or 2 two decks that match the playstyle you want to play. Then start playing!</p>

<h2>There Are Too Many Games to List!</h2>

<p>Warhammer board gaming is a lot bigger than you may think. Games Workshop has consistently released Warhammer board games (good and bad) over the years using the IP to get new players into the universe. Most games haven't made headlines and honestly most aren't good, but each of them has paved the way for better games to take their place.</p>

<p>I had another 10 Warhammer games I could have listed, but this article would be over 10,000 words. Maybe in a part 2 we can explore more games and even some deep cut games worth your time that you probably never heard of. To finish this article, I will offer you some superlatives for each of these games so you can see which one fits your taste the most.</p>

<ul>
  <li><strong>Most Likely To Cause A Real Life Fight:</strong> Forbidden Stars</li>
  <li><strong>Best Game to Show to a Magic Player:</strong> Warhammer Underworlds</li>
  <li><strong>Best Weekday Game Night Game:</strong> Blood Bowl Team Manager</li>
  <li><strong>Most likely to have Laugh Out Loud Moments:</strong> Blood Bowl</li>
  <li><strong>Least Church Friendly Board Game:</strong> Chaos in The Old World</li>
</ul>

<p>Thanks for reading! Please check out our previous articles on <a href="https://thrifthammer.com/blog/cheap-warhammer-miniatures-target/">Target Warhammer Board Games</a> and <a href="https://thrifthammer.com/blog/3-best-3-worst-warhammer-video-games/">The 3 Best (and worst) Warhammer Video Games</a>. If you are into this type of article these might be of interest to you.</p>
"""


class Command(BaseCommand):
    """Publish the Warhammer board games blog post (idempotent)."""

    help = 'Publishes the Warhammer board games blog post.'

    def add_arguments(self, parser):
        """Add --force flag."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing post body/meta. Never changes published_at.',
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Set status to PUBLISHED. Without this flag the post is created as a DRAFT (not visible on the live site).',
        )

    def handle(self, *args, **options):
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()
        status = Post.STATUS_PUBLISHED if options['publish'] else Post.STATUS_DRAFT

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) -- skipping.')
            )
            return

        body = BODY.format(
            blood_bowl_img=_static('images/blog/warhammer-board-games-blood-bowl.webp'),
            team_manager_img=_static('images/blog/warhammer-board-games-blood-bowl-team-manager.webp'),
            chaos_old_world_img=_static('images/blog/warhammer-board-games-chaos-in-the-old-world.webp'),
            forbidden_stars_img=_static('images/blog/warhammer-board-games-forbidden-stars.webp'),
            underworlds_img=_static('images/blog/warhammer-board-games-underworlds.webp'),
        )

        defaults = dict(
            slug=SLUG,
            title="Top 5 Warhammer Board Games Worth Your Time & Money",
            excerpt=(
                "A ranked look at the best Warhammer board games, from Blood Bowl to Warhammer "
                "Underworlds, covering gameplay, pricing, and where to find each one."
            ),
            body=body,
            status=status,
            # published_at is NOT here -- it never belongs in defaults
            meta_title='Top 5 Warhammer Board Games Worth Your Time & Money',
            meta_description=(
                "The 5 best Warhammer board games ranked: Blood Bowl, Team Manager, Chaos in "
                "the Old World, Forbidden Stars, and Underworlds, with pricing and where to buy."
            ),
            featured_image_url=_static('images/blog/warhammer-board-games-header.webp'),
            featured_image_alt='Stack of Warhammer board games: Blood Bowl, Forbidden Stars, Warhammer Underworlds, Blood Bowl Team Manager, and Chaos in the Old World',
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            post = existing
            self.stdout.write(self.style.SUCCESS(f'Updated post (pk={post.pk}), status={status}.'))
        else:
            # published_at is ONLY set here, on the creation path
            post = Post(**defaults, published_at=timezone.now())
            post.save()
            self.stdout.write(self.style.SUCCESS(f'Created post (pk={post.pk}), status={status}.'))

        tag_names = ['Reviews', 'Board Games']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags: {tag_names}'))
