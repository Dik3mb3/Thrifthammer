"""
Management command to publish the Best Warhammer 40K Books reading guide.

Idempotent — skips if the post already exists unless --force is passed.
Run AFTER collectstatic so staticfiles_storage resolves hashed image URLs.
"""

import datetime

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post, Tag

SLUG = 'best-warhammer-40k-books'
TITLE = 'Best Warhammer 40K Books: A Complete Reading Guide'
BASE_URL = 'https://thrifthammer.com'


class Command(BaseCommand):
    """Publish the Warhammer 40K books reading guide."""

    help = 'Publish the Best Warhammer 40K Books reading guide'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post if it already exists.',
        )

    def _static(self, path):
        """Return the absolute static URL for a committed image, or empty string if missing."""
        try:
            return f'{BASE_URL}{staticfiles_storage.url(path)}'
        except Exception:
            return ''

    def handle(self, *args, **options):  # noqa: C901
        existing = Post.objects.filter(slug=SLUG).first()
        if existing and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'Post already exists (slug={SLUG!r}). Use --force to overwrite.'
                )
            )
            return

        tag_beginner, _ = Tag.objects.get_or_create(
            name='Beginner Guide',
            defaults={'slug': 'beginner-guide'},
        )

        # ── Image URLs (resolved after collectstatic) ──────────────────────────
        collage_img      = self._static('images/blog/books-collage.jpg')
        horus_img        = self._static('images/blog/books-horus-rising.jpg')
        infinite_img     = self._static('images/blog/books-infinite-divine.jpg')
        eisenhorn_img    = self._static('images/blog/books-eisenhorn.jpg')
        ghazghkull_img   = self._static('images/blog/books-ghazghkull-thraka.jpg')
        elemental_img    = self._static('images/blog/books-elemental-council.jpg')
        gotrek_img       = self._static('images/blog/books-gotrek-felix.jpg')
        titanicus_img    = self._static('images/blog/books-titanicus.jpg')
        space_wolf_img   = self._static('images/blog/books-space-wolf.jpg')
        last_church_img  = self._static('images/blog/books-tales-of-heresy.jpg')

        def cover(url, alt, w=230, h=345):
            """Render a centred book-cover image block."""
            if not url:
                return ''
            return (
                f'<div style="text-align:center;margin:1.75rem auto 2rem;">'
                f'<img src="{url}" alt="{alt}" '
                f'style="max-width:{w}px;width:100%;border-radius:4px;'
                f'box-shadow:0 6px 24px rgba(0,0,0,0.5);" '
                f'width="{w}" height="{h}" loading="lazy">'
                f'</div>'
            )

        def amz(url, label='Buy on Amazon →'):
            """Render a small Amazon buy link."""
            return (
                f'<p style="margin-top:0.75rem;">'
                f'<a href="{url}" target="_blank" rel="noopener noreferrer sponsored"'
                f' style="color:var(--accent-gold-lt);font-weight:600;">{label}</a>'
                f'</p>'
            )

        # ── Post body ──────────────────────────────────────────────────────────
        body = f"""
<p>The Warhammer 40K universe is not just about epic battles and mighty villains. It is a vast setting filled with rich lore and incredible stories. Whether you are brand new to Warhammer 40K or a seasoned veteran, there are countless books to explore in this universe.</p>

<p>This guide highlights some of the best stories in the setting, exploring themes ranging from heroism and sacrifice to betrayal and Warhammer's favourite theme: grim irony. Brief synopses are provided for each to avoid spoilers.</p>

<hr>

<h2>How to Find Them</h2>

<p>Warhammer books have become more mainstream over the last few decades, with <em>A Thousand Sons</em> becoming the first Warhammer book to reach the <strong>New York Times Bestseller list</strong> in 2010. However, collecting a full physical library can be difficult, especially for older out-of-print novels.</p>

<p>All Amazon links in this guide are affiliate links (we earn a small commission at no extra cost to you).</p>

<hr>

<h2>The Best Series of 40K Novels</h2>

<h3>Horus Heresy Series (2006-2024)</h3>
{cover(horus_img, 'Horus Rising book cover, The Horus Heresy series by Dan Abnett')}
<p><strong>Authors:</strong> Dan Abnett, Graham McNeill, Aaron Dembski-Bowden, John French, Chris Wraight</p>
<p><a href="https://amzn.to/4eEVOm6" target="_blank" rel="noopener noreferrer sponsored">Paperback</a> | <a href="https://amzn.to/4e08W58" target="_blank" rel="noopener noreferrer sponsored">E-Book</a> | <a href="https://amzn.to/4cFRbWA" target="_blank" rel="noopener noreferrer sponsored">Audiobook</a></p>
<p><strong>Synopsis:</strong> A father and son are pitted against each other due to the meddling of mysterious entities known as Chaos, resulting in a brutal civil war in the 31st millennium.</p>
<p><strong>Sales pitch:</strong> The main Warhammer 40K series spanning over 50 novels. It spawned an entire standalone game system and remains Games Workshop's best-selling book series to date.</p>
<p><strong>Best for:</strong> Loreheads and those already familiar with the 40K universe. The Horus Heresy's grim irony lands hardest once you already understand the current state of the Imperium, so best read once you are hooked and ready to commit to a massive series. Start with <em>Horus Rising</em>, which remains one of the best entries even 20 years on.</p>

<hr>

<h2>Best Overall Novel</h2>

<h3>The Infinite and the Divine (2020)</h3>
{cover(infinite_img, 'The Infinite and the Divine book cover by Robert Rath')}
<p><strong>Author:</strong> Robert Rath</p>
<p><a href="https://amzn.to/41HSFdV" target="_blank" rel="noopener noreferrer sponsored">Paperback</a> | <a href="https://amzn.to/41Hcban" target="_blank" rel="noopener noreferrer sponsored">E-Book</a> | <a href="https://amzn.to/3QPzM6i" target="_blank" rel="noopener noreferrer sponsored">Audiobook</a></p>
<p><strong>Synopsis:</strong> Two ancient Necron rivals engage in a bitter 10,000-year feud over a mysterious artefact. Their petty rivalry escalates over time, reshaping the world around them as their obsession with outsmarting each other spirals out of control.</p>
<p><strong>Sales pitch:</strong> A cosmic dramedy that successfully humanises the most inhuman faction in Warhammer 40K. This book is widely credited with driving the rising popularity of the Necron faction on the tabletop. It is that good.</p>
<p><strong>Best for:</strong> Readers who want a little bit of everything. <em>The Infinite and the Divine</em> delivers the perfect formula of comedy, drama, and action, touching on all the grimdark and comedic aspects that make Warhammer great. If you are already familiar with 40K and do not know where to start, this is the book to read today.</p>

<hr>

<h2>Best Novel for Beginners</h2>

<h3>Eisenhorn Trilogy (2001-2002)</h3>
{cover(eisenhorn_img, 'Eisenhorn The Omnibus book cover by Dan Abnett')}
<p><strong>Author:</strong> Dan Abnett</p>
<p><a href="https://amzn.to/4tzFDuY" target="_blank" rel="noopener noreferrer sponsored">Paperback</a> | <a href="https://amzn.to/41L6OqI" target="_blank" rel="noopener noreferrer sponsored">E-Book</a></p>
<p><strong>Synopsis:</strong> An inquisitor's investigation into heresy sets off a chain of events that slowly transforms him from a zealous protector of the Imperium to collaborating with the very people he once held in contempt.</p>
<p><strong>Sales pitch:</strong> Do you enjoy hard-boiled detective stories or police procedurals? The Eisenhorn Trilogy might be for you. An approachable and grounded mystery-thriller focused more on character development and uncovering secrets than on massive galactic battles.</p>
<p><strong>Best for:</strong> Newcomers and non-Warhammer fans. Essentially a detective story, the Eisenhorn trilogy is one of the easiest entry points into the Warhammer setting, using familiar storytelling tropes that any reader can pick up and enjoy.</p>

<hr>

<h2>Most Fun Novel</h2>

<h3>Ghazghkull Thraka: Prophet of the Waaagh! (2021)</h3>
{cover(ghazghkull_img, 'Ghazghkull Thraka: Prophet of the Waaagh! book cover by Nate Crowley')}
<p><strong>Author:</strong> Nate Crowley</p>
<p><a href="https://amzn.to/4mE2WkO" target="_blank" rel="noopener noreferrer sponsored">Paperback</a> | <a href="https://amzn.to/3QhCQbn" target="_blank" rel="noopener noreferrer sponsored">E-Book</a> | <a href="https://amzn.to/4vIAlij" target="_blank" rel="noopener noreferrer sponsored">Audiobook</a></p>
<p><strong>Synopsis:</strong> A legendary grot tells the story of Ghazghkull Thraka and his rise from an Ork brute to uniting the Ork clans under one banner against the Imperium.</p>
<p><strong>Sales pitch:</strong> Do you want more <em>krumpin'</em> in your Warhammer stories? Are you a Gork or Mork believer? Are you confused but intrigued by what any of that means? Read this dark comedy to find out.</p>
<p><strong>Best for:</strong> Waaagh! enthusiasts and dark comedy fans. Chaotic storytelling, an unreliable narrator, and a completely unique perspective away from the usual Imperial viewpoint. If you want to dive into Ork culture and do not take Warhammer too seriously, this is a perfect entry point.</p>

<hr>

<h2>Most Underrated Novel</h2>

<h3>Elemental Council (2024)</h3>
{cover(elemental_img, 'Elemental Council audiobook cover, a T\'au Empire audiobook by Noah Van Nguyen')}
<p><strong>Author:</strong> Noah Van Nguyen</p>
<p><a href="https://amzn.to/4cWZYEE" target="_blank" rel="noopener noreferrer sponsored">Paperback</a> | <a href="https://amzn.to/4cx0yHW" target="_blank" rel="noopener noreferrer sponsored">E-Book</a> | <a href="https://amzn.to/4cDPPvx" target="_blank" rel="noopener noreferrer sponsored">Audiobook</a></p>
<p><strong>Synopsis:</strong> A T'au-ruled Imperial planet is on the brink of rebellion. To outmanoeuvre a crafty insurgent leader, a team of different T'au caste members is assembled to quash the uprising.</p>
<p><strong>Sales pitch:</strong> A hidden gem. A phenomenal mixture of action and political intrigue that expands the lore of a misunderstood and unique faction. If you have been disappointed by T'au books in the past, this is the standout novel the faction deserves.</p>
<p><strong>Best for:</strong> Political intrigue readers. If you enjoy espionage, internal politics, and exploring ideological conflict, this book is for you. The parallels to real-world competing philosophies and societal conflicts make it feel surprisingly relevant.</p>

<hr>

<h2>Best Warhammer Fantasy Novel</h2>

<h3>Gotrek &amp; Felix Series (1999-2015)</h3>
{cover(gotrek_img, 'Gotrek and Felix: The First Omnibus book cover by William King')}
<p><strong>Authors:</strong> William King, Nathan Long</p>
<p><a href="https://amzn.to/4clNJ4u" target="_blank" rel="noopener noreferrer sponsored">Paperback</a> | <a href="https://amzn.to/42g0I1E" target="_blank" rel="noopener noreferrer sponsored">E-Book</a></p>
<p><strong>Synopsis:</strong> Poet and human swordsman Felix follows Dwarf Slayer Gotrek across the Old World, recording his adventures as Gotrek seeks to accomplish his life's goal: a glorious death in battle.</p>
<p><strong>Sales pitch:</strong> An action-packed hack-and-slash adventure. A video game come to life, with constant, splashy, and enjoyable combat and a charming story that is easy for any reader to pick up.</p>
<p><strong>Best for:</strong> Light reading. <em>Gotrek and Felix</em> will not pose many deep philosophical questions, but the series is an absolute blast. Experience bloody battles against trolls, dragons, and other horrors across the Warhammer Fantasy world. Easy to drop in and out of whenever 40K gets too heavy.</p>

<hr>

<h2>Best Action Novel</h2>

<h3>Titanicus (2008)</h3>
{cover(titanicus_img, 'Titanicus audiobook cover by Dan Abnett, Sabbat Worlds')}
<p><strong>Author:</strong> Dan Abnett</p>
<p><a href="https://amzn.to/48f6ofN" target="_blank" rel="noopener noreferrer sponsored">E-Book</a> | <a href="https://amzn.to/4cWd4SI" target="_blank" rel="noopener noreferrer sponsored">Audiobook</a></p>
<p><strong>Synopsis:</strong> God-machines known as Titans clash in city-destroying battles as they fight to repel Chaos counterparts threatening the Imperium.</p>
<p><strong>Sales pitch:</strong> Giant stompy robots fighting other giant stompy robots, complete with spikes and mutations. What could be more cinematic? Beneath the spectacle is a fascinating exploration of the Adeptus Mechanicus, a cult that worships machines and the mysterious Omnissiah.</p>
<p><strong>Best for:</strong> Action readers and AdMech or Imperial Knights fans. On the surface, <em>Titanicus</em> is a classic action-heavy novel filled with cinematic destruction. But if you are interested in AdMech or Knight lore, it becomes far deeper, offering insight into factions not widely explored elsewhere.</p>

<hr>

<h2>Best Young Adult / Teen Novel</h2>

<h3>Space Wolf (1999)</h3>
{cover(space_wolf_img, 'Space Wolf 20th Anniversary Edition book cover by William King')}
<p><strong>Author:</strong> William King</p>
<p><strong>Synopsis:</strong> A young warrior is taken from his tribal world and inducted into the Space Wolves chapter. He undergoes brutal physical and mental trials on his journey to becoming a Space Marine.</p>
<p><strong>Sales pitch:</strong> A classic coming-of-age story with more brutality and far more action. <em>Space Wolf</em> explores identity, self-discipline, and loyalty, themes younger audiences can relate to. Do not worry, adults: this still retains all the core elements of a great Warhammer story.</p>
<p><strong>Best for:</strong> Young adults and newcomers. Most Warhammer books are not teen-friendly, often being too graphic or exploring very dark themes. <em>Space Wolf</em> strikes a balance, combining familiar YA themes with the grimdark edge of Warhammer. A solid entry point for adult newcomers too.</p>
<p><a href="https://amzn.to/4mGNc0g" target="_blank" rel="noopener noreferrer sponsored">E-Book</a></p>

<hr>

<h2>Best Short Story</h2>

<h3>The Last Church (2009)</h3>
{cover(last_church_img, 'Tales of Heresy anthology cover, containing The Last Church by Graham McNeill', w=230, h=310)}
<p><strong>Author:</strong> Graham McNeill</p>
<p><strong>Synopsis:</strong> On the eve of the Emperor's unification of Terra, a priest defends the last remaining church against a mysterious visitor who challenges the very foundation of religion.</p>
<p><strong>Sales pitch:</strong> Tired of constant superhuman battles? <em>The Last Church</em> is a breath of fresh air. A philosophical debate disguised as a short story, it explores the merit and influence of religion on humanity. This is not a fun romp across the galaxy. It is a serious, reflective piece that stays with you.</p>
<p><strong>Best for:</strong> Readers interested in themes and ideas. Perfect for anyone wanting a thought-provoking story that still hits hard. Especially impactful if you are already familiar with the Emperor of Mankind and the broader history of the Imperium.</p>
<p><a href="https://amzn.to/4sMMlwD" target="_blank" rel="noopener noreferrer sponsored">E-Book</a></p>

<hr>

<h2>Best Non-Novel</h2>

<h3>Faction Codices</h3>
<p><strong>Author:</strong> Games Workshop</p>
<p><strong>Synopsis:</strong> Faction-specific rulebooks containing gameplay mechanics, artwork, and lore that flesh out the Warhammer 40K universe from the perspective of each faction.</p>
<p><strong>Sales pitch:</strong> Some factions starve for lore. Most novels you will find lean heavily human-centric, focusing on Space Marines and Imperial Guard. Faction Codices are a great way to access faction-specific lore for underrepresented armies. If you enjoy grimdark artwork, the visuals alone make them worth flipping through.</p>
<p><strong>Best for:</strong> Tabletop players and lore collectors. Older codices are packed with artwork and depth, making them great additions to any library. Browse eBay or secondhand stores, where used codices can often be found at very reasonable prices.</p>

<hr>

<h2>Community Picks</h2>

<p>A few additional series that came highly recommended by the communities I surveyed. These did not make my personal top list only because I have not finished them yet, but they are widely loved:</p>

<ul>
<li><a href="https://amzn.to/4u4uPoS" target="_blank" rel="noopener noreferrer sponsored"><strong>Gaunt's Ghosts Series (1999-2019)</strong></a> by Dan Abnett</li>
<li><a href="https://amzn.to/3OOrKtU" target="_blank" rel="noopener noreferrer sponsored"><strong>Ciaphas Cain Series (2003-2018)</strong></a> by Alex Stewart</li>
<li><a href="https://amzn.to/4tZFNvE" target="_blank" rel="noopener noreferrer sponsored"><strong>Night Lords Trilogy (2010-2012)</strong></a> by Aaron Dembski-Bowden</li>
<li><a href="https://amzn.to/48NQ4Tt" target="_blank" rel="noopener noreferrer sponsored"><strong>Fabius Bile Series (2016-2020)</strong></a> by Joshua Reynolds</li>
<li><a href="https://amzn.to/4tkxaf9" target="_blank" rel="noopener noreferrer sponsored"><strong>Path of the Dark Eldar Series (2012-2014)</strong></a> by Andy Chambers</li>
</ul>

<p>Shoutout to <a href="https://www.reddit.com/r/DealHammer/" target="_blank" rel="noopener noreferrer">r/DealHammer</a> and <a href="https://www.reddit.com/r/Warhammer/" target="_blank" rel="noopener noreferrer">r/Warhammer</a> for the help.</p>

<hr>

<h2>Conclusion</h2>

<p>Whichever series you choose to start with, you are in for a great journey. The Warhammer universe is so vast that there are countless entry points to explore. If you still cannot decide, lore videos on YouTube are a great way to get a feel for different factions and time periods before committing to a book.</p>

<p>If you already play the tabletop game, start with the faction or system you enjoy most, whether that is 40K, Age of Sigmar, The Old World, Necromunda, or something else entirely. There are books tied to every Warhammer game system.</p>

<p>While there are definitely some weaker entries in the Warhammer library, there are dozens of fantastic books not mentioned here that could end up being your personal favourite. Have fun discovering the universe, and this list will be updated as more books get read and reviewed.</p>
"""

        published_dt = datetime.datetime(2026, 4, 19, 12, 0, 0, tzinfo=datetime.timezone.utc)

        post, created = Post.objects.update_or_create(
            slug=SLUG,
            defaults={
                'title': TITLE,
                'author': 'ThriftHammer',
                'excerpt': (
                    'A curated guide to the best Warhammer 40K books, from the epic '
                    'Horus Heresy to hidden gems like Elemental Council. Picks for every '
                    'type of reader, from beginners to lore veterans.'
                ),
                'body': body,
                'status': Post.STATUS_PUBLISHED,
                'published_at': published_dt,
                'featured_image_url': collage_img,
                'featured_image_alt': (
                    'Collage of the best Warhammer 40K book covers including Horus Rising, '
                    'Eisenhorn, Ghazghkull Thraka, and more'
                ),
                'meta_title': 'Best Warhammer 40K Books: A Complete Reading Guide',
                'meta_description': (
                    'The best Warhammer 40K books for every type of reader. From Horus Rising '
                    'to Eisenhorn. Find the perfect entry point into the 40K universe.'
                ),
            },
        )
        post.tags.set([tag_beginner])

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action}: {post.title}'))
        self.stdout.write(f'  Slug: {post.slug}')
        self.stdout.write(f'  Featured image: {post.featured_image_url or "(none — run after collectstatic)"}')
