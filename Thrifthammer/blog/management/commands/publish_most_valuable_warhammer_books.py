"""
Management command: publish_most_valuable_warhammer_books

Creates 'The Most Expensive, Rare & Sought After Warhammer Books Ever
Released' blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_most_valuable_warhammer_books
    python manage.py publish_most_valuable_warhammer_books --force
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'most-valuable-warhammer-books'
SITE_URL = 'https://thrifthammer.com'


def _static(path):
    try:
        return f'{SITE_URL}{staticfiles_storage.url(path)}'
    except Exception:
        return ''


def _gallery(gallery_id, images):
    """Return a swipeable (scroll-snap) image gallery, no JS required for the swipe itself."""
    slides = '\n'.join(
        f'    <div class="mvb-gallery-slide" id="{gallery_id}-{i + 1}">'
        f'<img src="{src}" alt="{alt}" width="{w}" height="{h}" loading="lazy"></div>'
        for i, (src, alt, w, h) in enumerate(images)
    )
    dots = '\n'.join(
        f'    <a href="#{gallery_id}-{i + 1}" class="mvb-gallery-dot{" mvb-gallery-dot-active" if i == 0 else ""}" '
        f'aria-label="Image {i + 1} of {len(images)}"></a>'
        for i in range(len(images))
    )
    return (
        f'<div class="mvb-gallery" data-gallery="{gallery_id}">\n'
        f'  <div class="mvb-gallery-track" id="{gallery_id}-track">\n'
        f'{slides}\n'
        f'  </div>\n'
        f'  <div class="mvb-gallery-nav">\n'
        f'{dots}\n'
        f'  </div>\n'
        f'</div>'
    )


_BASE = 'https://thrifthammer.com/static/images/blog'

PRIMARCH_GALLERY = _gallery('primarch', [
    (f'{_BASE}/most-valuable-warhammer-books-primarch-series-set-1.webp',
     'Complete 18-volume Horus Heresy Primarchs limited edition book set standing upright, showing spines with Primarch names and legion icons',
     813, 577),
    (f'{_BASE}/most-valuable-warhammer-books-primarch-series-set-2.webp',
     "Angled view of Horus Heresy Primarchs limited edition spines including Vulkan, Lorgar, Sanguinius, Alpharius, Rogal Dorn, Mortarion, Ferrus Manus, Jaghatai Khan, and Corax",
     782, 469),
    (f'{_BASE}/most-valuable-warhammer-books-primarch-series-set-3.webp',
     "Horus Heresy Primarchs limited edition spines including Perturabo, Roboute Guilliman, Leman Russ, Fulgrim, Magnus the Red, Konrad Curze, Lion El'Jonson, and Angron",
     914, 610),
    (f'{_BASE}/most-valuable-warhammer-books-primarch-series-covers-1.webp',
     'Close-up of two Horus Heresy Primarchs limited edition book covers with gold and purple foil artwork',
     1000, 625),
    (f'{_BASE}/most-valuable-warhammer-books-primarch-series-covers-2.webp',
     'Close-up of two Horus Heresy Primarchs limited edition book covers with teal serpent and gold Imperial Fists foil artwork',
     1000, 597),
    (f'{_BASE}/most-valuable-warhammer-books-primarch-series-covers-3.webp',
     "Close-up of two Horus Heresy Primarchs limited edition book covers with red Lion El'Jonson and orange Konrad Curze foil artwork",
     997, 624),
])

SIEGE_GALLERY = _gallery('siege', [
    (f'{_BASE}/most-valuable-warhammer-books-siege-of-terra-single-volume.webp',
     "The Horus Heresy: Siege of Terra, The End and the Death Volume I, limited edition leather bound book with gold Imperial Fists emblem",
     554, 554),
    (f'{_BASE}/most-valuable-warhammer-books-siege-of-terra-spines.webp',
     "Ten Horus Heresy Siege of Terra limited edition book spines, including The Defence of the Lion's Gate, The Imperial Palace, and The Vengeful Spirit",
     900, 847),
    (f'{_BASE}/most-valuable-warhammer-books-siege-of-terra-full-set.webp',
     'Complete 14-volume Horus Heresy Siege of Terra hardback book set lined up on a shelf',
     1000, 407),
])

LIBER_GALLERY = _gallery('liber', [
    (f'{_BASE}/most-valuable-warhammer-books-liber-chaotica-four-volumes.webp',
     'Four individual Liber Chaotica volumes dedicated to Khorne, Slaanesh, Nurgle, and Tzeentch, each with themed Chaos god cover art',
     375, 500),
    (f'{_BASE}/most-valuable-warhammer-books-liber-chaotica-complete-edition.webp',
     'Liber Chaotica Complete Edition hardcover book with gold foil chaos star design',
     375, 500),
])

BODY = """\
<style>
/* -- Most Valuable Warhammer Books post ---------------------------------- */

/* Swipeable image gallery -- native CSS scroll-snap, no JS required to swipe */
.mvb-gallery { margin: 1.25rem 0; }
.mvb-gallery-track {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  border-radius: 10px;
  background: #111318;
}
.mvb-gallery-track::-webkit-scrollbar { display: none; }
.mvb-gallery-slide {
  flex: 0 0 100%;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mvb-gallery-slide img {
  width: 100%;
  height: auto;
  max-height: 420px;
  object-fit: contain;
  display: block;
}
.mvb-gallery-nav {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.65rem;
}
.mvb-gallery-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.22);
  display: inline-block;
}
.mvb-gallery-dot-active { background: #c8922a; }

.mvb-hero-img { display: block; width: 100%; max-width: 360px; height: auto; margin: 1.25rem auto; border-radius: 8px; }
</style>

<p>Warhammer books are the most affordable way to be part of the Warhammer community and universe. The first Warhammer novel, Drachenfels, released in 1989, followed by the first Warhammer 40,000 book, Inquisitor (later renamed Draco), in 1990. Over 670 books have been released through the Black Library, many belonging to legendary series like the Horus Heresy, Ciaphas Cain, Gaunt's Ghosts, and the Eisenhorn series.</p>

<p>Did you know that some Warhammer books have reached even higher levels of legendary status? If you have been around long enough, you may currently possess one of the few rare Warhammer book releases that routinely sell for hundreds and sometimes even thousands of dollars today. Their collector value has been going up exponentially over the years.</p>

<p>Today we are going to explore four of the rarest and most expensive Warhammer books currently available. From the depths of the Black Library to limited print runs of the most popular and easily accessible Warhammer books, let's look at some of the rarest real-life Warhammer relics you can own. There will be future parts, because this was not only fun to research, but also very educational in understanding the world of collecting. These are ranked by how much I personally enjoyed the story behind the books, and how interested I would be in obtaining the book myself.</p>

<h2>How did these books become so expensive?</h2>

<p>Unlike traditional novel publishing, which produces millions of copies at low entry level prices, Black Library often releases highly limited collector editions. Many of these premium releases are individually numbered and feature exclusive artwork, often including premium components like ribbon bookmarks, leatherette covers, author signatures, or slipcases. They are both fancy and limited in stock, so they can disappear within minutes of preorders opening, creating a rabid market of secondary buyers.</p>

<p>Once these editions sell out, the only way to obtain them is through the secondary market, where prices are determined entirely by collector demand. Over time, as supply dries up, either due to books deteriorating or a lack of sellers, prices go up, growing exponentially as time passes. Games Workshop has no incentive to reprint these releases, leading to growing prices over time, like we see in other hobbies such as TCGs, baseball cards, and sports memorabilia.</p>

<p><strong>The factors that influence value:</strong></p>
<ul>
  <li>How limited the original print run was</li>
  <li>Book/author popularity; authors like Dan Abnett are far more popular</li>
  <li>What book series they are part of</li>
  <li>Unique selling points (author signatures, being numbered, etc.)</li>
  <li>How beautiful the book is</li>
  <li>Book condition</li>
</ul>

<p>As Warhammer continues growing worldwide, collector demand is increasing, making many older Black Library editions significantly more valuable than their original retail price. According to Grand View Research and Spherical Insights, as of 2025 the collectibles and memorabilia industry is valued between $320 billion and $490 billion. With popular collector markets like baseball cards already mature and highly valued (this author would argue overvalued), there are collectors, both within and outside the community, looking to grab these treasures as assets expected to appreciate in value.</p>

<h2>1. Dark Hunters: Umbra Sumus</h2>

<img class="mvb-hero-img" src="{_BASE}/most-valuable-warhammer-books-dark-hunters-cover.webp" alt="Warhammer 40,000 Dark Hunters: Umbra Sumus novel cover by Paul Kearney featuring Dark Hunters Space Marines in battle" width="360" height="555" loading="lazy">

<h3>Current Market Value</h3>
<ul>
  <li>Only one copy is publicly available for <a href="https://www.ebay.com/itm/157323435366" target="_blank" rel="noopener noreferrer">$70,000+</a></li>
  <li>Rumors of private auctions valuing it in the thousands</li>
</ul>

<p>Released: 2025 | Author: Paul Kearney</p>

<h3>Why It's Valuable</h3>
<ul>
  <li>Only a handful of copies ever made it to consumer hands (rumored to be less than 200 copies floating around) due to the book being withdrawn over a copyright issue</li>
  <li>A "Holy Grail" book shrouded in mystery and intrigue, as copies are rarely seen publicly. There is nothing to compare it to, it's unique.</li>
  <li>The story behind the book is just as interesting as the book itself.</li>
</ul>

<h3>Book Features</h3>
<ul>
  <li>Nothing! This is a normal Black Library book.</li>
</ul>

<h3>Community Reception</h3>

<p>The small portion of people who have actually read the digital version of the book have an overall positive sentiment about it. Goodreads rates the book 3.9/5, probably a fair rating for a book about a fringe successor chapter with no major impact on the setting and the Warhammer universe. However, this has to be one of the most fun stories I have researched. That Games Workshop, a multimillion-dollar juggernaut, gave up a legal battle immediately and then didn't even rename the book to release it is wild to me. Dark Hunters is not the most creative name to begin with; wouldn't Dark Stalkers or Night Hunters work fine as a title? Couldn't the lawyers and creatives come together to find a solution and release the book at a later date?</p>

<p>I guess not, but if you want to read the novel you can find it for free <a href="https://i.4pcdn.org/tg/1481647542114.pdf" target="_blank" rel="noopener noreferrer">here</a>. It's suspected (but not confirmed) that the author Paul Kearney leaked the book online after being left out to dry by Games Workshop. I feel really bad for Mr. Kearney, who put a ton of effort into what seems to be a solid book without being financially rewarded for it. I would recommend reading this novel not just for the story, but also to be part of history, reading a book that was never supposed to exist publicly in the first place. Once I read the story behind the book and the insane prices it's selling for, I immediately added it to the top of my reading list.</p>

<h3>Fun Facts &amp; Trivia</h3>
<ul>
  <li>A digital version of this book exists, so the story is not lost and is available for any interested reader</li>
  <li>The copyright dispute was over the title "Dark Hunters," which apparently infringed on Sherrilyn Kenyon's long-running Dark Hunter fantasy series</li>
  <li>Games Workshop never fought the copyright in court and instead gave up on releasing it entirely, accidentally creating one of the rarest books in all of existence</li>
</ul>

<h2>2. Primarch Series Limited Edition Complete Set [18 Volumes]</h2>

{primarch_gallery}

<h3>Current Market Value</h3>
<ul>
  <li><a href="https://www.ebay.com/itm/336593454437?_skw=primarch+series+warhammer+40K+edition+complete" target="_blank" rel="noopener noreferrer">$8,299.99</a> for all 18 Volumes (eBay)</li>
  <li><a href="https://www.ebay.com/itm/198414853747?_skw=primarch+series+warhammer+40K+edition+complete" target="_blank" rel="noopener noreferrer">$5,715</a> for 11 Volumes (eBay)</li>
  <li>$200 to $500 per single volume</li>
</ul>

<p>Released: 2016 to 2023 | Authors: David Annandale, Chris Wraight, Graham McNeill, Guy Haley, Gav Thorpe, Josh Reynolds, David Guymer, Nick Kyme, Mike Brooks, Rob Sanders, Ian St. Martin, Andy Smillie, John French</p>

<h3>Why It's Valuable</h3>
<ul>
  <li>Only 2,500 copies were released per book (45,000 copies were released across the entire series)</li>
  <li>An entire set is significantly more expensive than collecting a few books, since the maximum number of sets possible at any time is 2,500 and most books are not currently part of completed sets</li>
  <li>Only includes Black Library novels dedicated to each Primarch, which are often the most popular, well loved books</li>
</ul>

<h3>Book Features</h3>
<ul>
  <li>Magnetic presentation box</li>
  <li>Cloth-wrapped spine with metallic foiling</li>
  <li>Gilded pages</li>
  <li>Ribbon marker</li>
  <li>Individually numbered on a special page</li>
</ul>

<h3>Best Books From The Series</h3>

<p>To be fair, I have not read all these books, but for me the standouts are:</p>
<ul>
  <li>Konrad Curze: The Night Haunter</li>
  <li>Magnus the Red: Master of Prospero</li>
  <li>Angron, Slave of Nuceria</li>
  <li>Alpharius, Head of the Hydra</li>
  <li>Jaghatai Khan, Warhawk of Chogoris</li>
</ul>

<h3>Community Reception</h3>

<p>Honestly, a mixed bag. In terms of physical quality, each of these books is absolutely beautiful, with so many tiny details and hidden features that make them so unique. The quality of the stories, less so.</p>

<p>There are amazing stories (see above) in this series, but also some stinkers. Roboute Guilliman: Lord of Ultramar and Vulkan: Lord of Drakes are notoriously disliked by a portion of the Warhammer community. This is especially disappointing, as Ultramarines are the poster boys of <a href="/products/?category=warhammer-40000&amp;faction=space-marines&amp;sort=discount">Space Marines</a>, the <a href="/blog/warhammer-40k-faction-popularity-ranking/">most popular Warhammer 40K faction</a>. To have your poster boy Primarch and number one Space Marine chapter be the stars of one of the least liked books in the series is definitely not a win for Games Workshop. A majority of the series probably won't rank in most people's top 10 books, so if the quality of the stories matters to you as much as the physical attributes, you may only want to collect your favorites from the series.</p>

<h3>Fun Facts &amp; Trivia</h3>
<ul>
  <li>The page edges of each book are gilded with colors that match each Primarch's Space Marine legion</li>
  <li>Vulkan: Lord of Drakes comes with scaly leather textures, a unique physical element for a limited edition book</li>
  <li>The cover of each book in the series is unique, with some books covered in script and others with legion-specific icons</li>
</ul>

<h2>3. The Siege of Terra Complete Set [14 Volumes]</h2>

{siege_gallery}

<h3>Current Market Value</h3>
<ul>
  <li>Estimated $6,000 to $8,000 for the limited edition set (14 volumes)</li>
  <li><a href="https://www.ebay.com/itm/116465472137" target="_blank" rel="noopener noreferrer">$2,420</a> for the hardback set (14 volumes)</li>
  <li>$200 to $400 per single limited edition volume</li>
</ul>

<p>Released: 2019 to 2025 | Authors: Dan Abnett, John French, Guy Haley, Gav Thorpe, Chris Wraight, Aaron Dembski-Bowden, Graham McNeill, James Swallow</p>

<h3>Why It's Valuable</h3>
<ul>
  <li>Only 2,500 copies were released per book in the series (are you catching a pattern?)</li>
  <li>Siege of Terra is a well regarded series by the community, partially authored by the always popular Dan Abnett</li>
  <li>Each book sold out in minutes when released; there was not enough time or stock to satisfy the demand. Unlike the Primarch series, there is a greater incentive to own every book in this closely knit series.</li>
</ul>

<h3>Book Features</h3>
<ul>
  <li>Premium leather binding</li>
  <li>Metallic reflective gilt page edges</li>
  <li>Foil artwork and stamping pressed into the leather</li>
  <li>Books have handwritten, serialized numbers</li>
  <li>High quality, heavy duty paper for book pages</li>
</ul>

<h3>Community Reception</h3>

<p>Overall, very positive. Online communities praise the series, with only some negative comments pointing out "slow parts" or certain books that did not appeal to them. The series definitely benefits from being partially penned by Dan Abnett, whose contributions are often considered the high points of the series. While Siege of Terra may not be the best book series Warhammer has to offer, there is no doubt it's worth a read, especially if you enjoy the Horus Heresy setting.</p>

<p>I would argue the limited editions of these books are the best of this group of novels we are going to explore in this article. There is something super classy yet so Warhammer about these limited edition boxes. The pressed leather bindings are pure quality, while not being as flashy as the gaudier (albeit very cool) limited edition Primarch books. I am a sucker for a nice leather bound book, and these would look striking on a bookshelf while not looking out of place next to non-Warhammer novels.</p>

<h3>Fun Facts &amp; Trivia</h3>
<ul>
  <li>The limited edition versions of these books were the way to get early access before anyone else could read them</li>
  <li>You can build a paperback collection of this series for under $300, and a hardback collection for $2K!</li>
  <li>The first book in the series, The Solar War, is often the most sought after book in the series and is increasingly rare</li>
</ul>

<h2>4. Liber Chaotica</h2>

{liber_gallery}

<h3>Current Market Value</h3>
<ul>
  <li>Over <a href="https://www.ebay.com/itm/116479929859?_skw=liber+chaotica+warhammer+limited+edition" target="_blank" rel="noopener noreferrer">$1,000</a> per copy</li>
  <li><a href="https://www.ebay.com/itm/137548260713?_skw=liber+chaotica+warhammer+limited+edition" target="_blank" rel="noopener noreferrer">$400</a> for the complete edition hardcover</li>
</ul>

<p>Released: 2003 to 2005 | Author: Richard Williams, John Blanche (artist)</p>

<h3>Why It's Valuable</h3>
<ul>
  <li>John Blanche's art, with the artist recently passing (rest in peace), means books with his art are likely to become even more valuable</li>
  <li>Limited to 300 numbered copies released over 20 years ago; as time passes, these books become rarer and finding one in pristine condition becomes harder</li>
  <li>Unique both in looks and perspective, with the book and story feeling more like an in-universe manuscript than a straightforward novel</li>
</ul>

<h3>Book Features</h3>
<ul>
  <li>Individually numbered copies on the original limited volumes</li>
  <li>Each single volume housed in a themed casing tied to its Chaos god (Khorne's volume encased in steel, Nurgle's in branded wood)</li>
  <li>John Blanche art</li>
</ul>

<h3>Community Reception</h3>

<p>It depends on whether you're a Fantasy enthusiast. For those interested in old lore, these books can be considered cult classics, even with Warhammer Fantasy dying out and being replaced by Age of Sigmar and Warhammer 40K. What intrigues me most about these books is how unusual they are, both in story and in how they look physically. Significant effort was put into mirroring the books' exterior to match the unusual "in-universe" perspective explored in the writing. These books were meant to feel like heretical scripture you could find stored in a secretive vault somewhere. They are extremely unique in that sense, and massive effort was put into crafting them into timeless collectables that hold value despite the universe they were based on crumbling over time.</p>

<p>If Dark Hunters was the most fun story we explored, Liber Chaotica is the most interesting for its place in Warhammer history. I don't know if the stories told in this book would hold up to the best Warhammer 40K books today, but as a tangible piece of Warhammer history, there is no doubt these are as cool as anything Games Workshop has released over the last 20 years. The community seems to agree: paperback versions of these books go for $50 apiece despite having no fancy features and lore with little connection to modern Warhammer. These books are a time capsule to Warhammer's past, and if you're even a little interested in Warhammer Fantasy, these books are worth seeking out, at least the more affordable paperback versions.</p>

<h3>Fun Facts &amp; Trivia</h3>
<ul>
  <li>The books were reprinted in 2019 as a "complete edition," which is the most accessible way to own it today</li>
  <li>Richard Williams reportedly worked as an accountant in London while writing some of the most deranged Chaos lore</li>
  <li>Liber Chaotica has a spiritual successor, Liber Necris, a companion sourcebook on the undead of the Warhammer world, published in a similar in-universe "forbidden text" style</li>
</ul>

<h2>Are there more of these rare books circulating?</h2>

<p>Heck yes! This article could have easily been double the length with more entries. I just condensed it to the few I thought were the most interesting. There will be a part two in the future featuring not just Black Library novels, but old rule books and RPG books that have been lost to time and are now worth big bucks. I am already bubbling with excitement to share the next installment.</p>

<p>For those looking for their next Warhammer book, at ThriftHammer we recently dropped a list of our <a href="/blog/best-warhammer-40k-books/">favorite Warhammer novels</a>. Check those out, you might find your next favorite book there. If you're interested in staying up to date on blog posts, miniature deals, and more, please sign up for the newsletter. That's the only way you will know when the next part of this new series will release.</p>
"""
BODY = (
    BODY
    .replace('{_BASE}', _BASE)
    .replace('{primarch_gallery}', PRIMARCH_GALLERY)
    .replace('{siege_gallery}', SIEGE_GALLERY)
    .replace('{liber_gallery}', LIBER_GALLERY)
)


class Command(BaseCommand):
    """Publish the Most Valuable Warhammer Books blog post (idempotent)."""

    help = 'Publishes the Most Valuable Warhammer Books blog post.'

    def add_arguments(self, parser):
        """Add --force flag."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing post body/meta. Never changes published_at.',
        )

    def handle(self, *args, **options):
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) -- skipping.')
            )
            return

        defaults = dict(
            slug=SLUG,
            title='The Most Expensive, Rare & Sought After Warhammer Books Ever Released',
            excerpt=(
                'Discover the rarest, most sought after Black Library books ever printed, '
                'including collector editions worth hundreds or thousands of dollars.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            # published_at is NOT here -- it never belongs in defaults
            meta_title='',
            meta_description=(
                'Discover the rarest, most sought after Black Library books ever printed, '
                'including collector editions worth hundreds or thousands of dollars.'
            ),
            featured_image_url=_static('images/blog/header_most-valuable-warhammer-books.webp'),
            featured_image_alt=(
                'A collage of four rare Warhammer books: the Dark Hunters novel cover, a '
                'Primarch limited edition cover, a Liber Chaotica cover, and the Fury of '
                'Magnus Siege of Terra volume'
            ),
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            post = existing
            self.stdout.write(self.style.SUCCESS(f'Updated post (pk={post.pk}).'))
        else:
            # published_at is ONLY set here, on the creation path
            post = Post(**defaults, published_at=timezone.now())
            post.save()
            self.stdout.write(self.style.SUCCESS(f'Created post (pk={post.pk}).'))

        tag_names = ['Warhammer 40K', 'Collecting', 'Black Library']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags: {tag_names}'))
