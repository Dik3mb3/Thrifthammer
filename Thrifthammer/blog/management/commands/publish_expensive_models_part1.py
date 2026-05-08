"""
Management command: publish_expensive_models_part1

Creates the 'Largest & Most Expensive Warhammer 40K Models: Part 1' blog post.
Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_expensive_models_part1
    python manage.py publish_expensive_models_part1 --force  # overwrite existing
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'most-expensive-largest-warhammer-40k-models-forge-world-resin'

IMG = '/static/img/blog/expensive-models'

STAT = (
    '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:0.75rem 2rem;'
    'background:var(--bg-elevated);border:1px solid var(--border-subtle);'
    'border-radius:8px;padding:1rem 1.5rem;margin:1.5rem 0;">'
    '{rows}</div>'
)

ROW = (
    '<div>'
    '<div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.07em;'
    'color:var(--text-muted);margin-bottom:0.2rem;">{label}</div>'
    '<div style="font-weight:{bold};{extra}">{val}</div>'
    '</div>'
)


def stat_card(price, size_label, size_val, components, points, rules_url):
    rows = (
        ROW.format(label='Price', bold='700',
                   extra='font-size:1.3rem;color:var(--accent-gold-lt);', val=price)
        + ROW.format(label=size_label, bold='600', extra='', val=size_val)
        + ROW.format(label='Components', bold='600', extra='', val=components)
        + ROW.format(
            label='In-Game Points', bold='600', extra='',
            val=(
                f'{points}&nbsp;&nbsp;'
                f'<a href="{rules_url}" target="_blank" rel="noopener noreferrer" '
                f'style="font-size:0.8rem;font-weight:400;">[Rules]</a>'
            )
        )
    )
    return STAT.format(rows=rows)


def model_img(filename, alt):
    return (
        '<div style="background:var(--bg-elevated);border-radius:8px;'
        'margin:1rem auto 1.75rem;max-width:600px;height:280px;'
        'display:flex;align-items:center;justify-content:center;overflow:hidden;">'
        f'<img src="{IMG}/{filename}" alt="{alt}" '
        'style="max-width:100%;max-height:100%;object-fit:contain;" '
        'loading="lazy" width="600" height="280">'
        '</div>'
    )


YOUTUBE_EMBED = """\
<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:2rem 0;border-radius:8px;">
  <iframe
    src="https://www.youtube.com/embed/SHg0RKppwEM"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;border-radius:8px;"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
    loading="lazy"
    title="Most Expensive Warhammer 40K Models: Warlord Titan vs Manta">
  </iframe>
</div>
"""

BODY = f"""\
<p>If you think normal Warhammer 40K is an expensive hobby, wait until you see some of the models we are talking about today. These aren't your normal $60 plastic kits. These are massive resin models that can cost more than some used cars! Welcome to the world of epic-sized model collecting, where size really does matter and the cost of buying a single model can be a normal player's entire annual hobby budget.</p>

<h2>What Is an Epic Sized Model?</h2>

<p>A standard Warhammer 40K model is traditionally anywhere from 28mm to 40mm (1 to 2 inches) in scale, often weighing 4 to 8 grams (0.1 to 0.5 ounces) if plastic or resin.</p>

<p>Epic sized models are measured in inches and feet (millimeters and centimeters) and often weigh more than a human toddler or small animal. These are not models that can be transported easily, nor are they particularly useful in games. These are statement pieces, collector items, and passion projects that 99% of players will never interact with.</p>

<p>The top 10 we are going to look at are all resin models, the largest, heaviest, and most expensive in the Warhammer catalog. Don't worry, we will tackle the top 10 most expensive and largest plastic models soon!</p>

<p>We excluded any models currently not sold on the Warhammer website. This includes the Mars-Alpha Pattern Volcano Cannon Warbringer Nemesis Titan ($1,700+) which would have easily made this list if it were available.</p>

<p>Now that we've covered what makes a model "epic" in Warhammer 40K, let's dive into the list.</p>

<h2>The Top 10</h2>

<ol>
  <li>Manta</li>
  <li>Mars Pattern Warlord Titan Body</li>
  <li>Legion Sokar Stormbird</li>
  <li>Mars Pattern Reaver Titan</li>
  <li>Legion Thunderhawk Gunship</li>
  <li>Acastus Knight Porphyrion</li>
  <li>Mars Pattern Warhound Titan</li>
  <li>Acastus Knight Asterius</li>
  <li>Mastodon Super-Heavy Assault Transport</li>
  <li>Legio Custodes Ares Gunship</li>
</ol>

<p><strong>Honorable Mention:</strong> Hierophant Bio-Titan</p>

<hr>

<h2>Honorable Mention: Hierophant Bio-Titan</h2>

{stat_card('$535', 'Length', '11 in / 280 mm', '40', '580 pts',
           'https://wahapedia.ru/wh40k10ed/factions/tyranids/Hierophant')}

{model_img('hierophant.jpeg', 'Hierophant Bio-Titan Forge World resin model')}

<p>This entry could have been the <a href="https://www.warhammer.com/en-US/shop/Tyranid-Harridan?queryID=cedb6394f42c0d07dcb6e724a0ba3419" target="_blank" rel="noopener noreferrer">Tyranid Harridan</a>, which also sells for $535, but this model is sick and since we are going to go through a ton of flyers, I decided to include this one. This model is too big to be useful on the tabletop (like most things on this list) but wow, it's so much fun! Design-wise, this is one of the most creative models on the list and the model's profile includes a Strength 20 talon melee attack. That is exactly what I want from a giant bug. This won't win you many games, but it is much cheaper and cooler than some of the other epic models we are going to look at.</p>

<h2>#10 Legio Custodes Ares Gunship</h2>

{stat_card('$575', 'Length', '1.14 ft / 250 mm', '80', '580 pts',
           'https://wahapedia.ru/wh40k10ed/factions/adeptus-custodes/Ares-Gunship')}

{model_img('ares-gunship.jpeg', 'Legio Custodes Ares Gunship Forge World resin model')}

<p>Not competitively viable, but an awesome model design, the Ares Gunship deserves a plastic kit. The only model on this list I have seen in person, and those I know who have built one have criticized the heavy chunks of resin that make it a nightmare to assemble. This is one of the few attainable models price-wise on the list, but the quality of the kit is not worth the price. Stick to the core Custodes units and wait for more plastic releases.</p>

<h2>#9 Mastodon Super-Heavy Assault Transport</h2>

{stat_card('$650', 'Length', '9.8 in / 250 mm', '196 (108 resin, 88 plastic)', '540 pts',
           'https://wahapedia.ru/hh2ed/factions/space-marines/Mastodon/')}

{model_img('mastodon.jpeg', 'Mastodon Super-Heavy Assault Transport Forge World resin model')}

<p>An odd mix of resin and plastic, the Mastodon is a weird kit. The transport doors, Skyreaper battery, siege melta array, and sponson weapons (heavy bolter, lascannon, heavy flamers, and volkite culverins) can all be assembled without glue. The Mastodon is essentially a massive <a href="/products/space-marine-land-raider-redeemer/">Land Raider</a> but lacks the same charm as its little cousin.</p>

<h2>#8 Acastus Knight Asterius</h2>

{stat_card('$660', 'Height', '9.8 in / 250 mm', '153', '765 pts',
           'https://wahapedia.ru/wh40k10ed/factions/imperial-knights/Acastus-Knight-Asterius')}

{model_img('acastus-knight-asterius.jpeg', 'Acastus Knight Asterius Forge World resin model')}

<p>The first of our many giant mechs, and honestly one of the most stylish. This model gives off the strongest Chaos Knight vibes of all the titans on the list. Sustained D3 twin conversion beam cannons is very fun, if a bit inconsistent. This model also has one of the weirdest niche rules I have seen in 40K. The Sunderer of Fortresses ability gives attacks from this model +1 strength and +1 damage against vehicles (totally normal), but oddly +2 strength and +2 damage against fortifications. I am not sure if Games Workshop has fully realized this, but fortifications are unfortunately dead on the tabletop, making half this ability essentially useless. Maybe in 11th edition fortifications will be a bit better? I hope so. I would love to see this knight in action.</p>

<h2>#7 Mars Pattern Warhound Titan</h2>

{stat_card('$695', 'Height', '9.8 in / 250 mm', '199', '840 pts',
           'https://wahapedia.ru/wh40k10ed/factions/adeptus-titanicus/Warhound-Titan')}

{model_img('warhound-titan.jpeg', 'Mars Pattern Warhound Titan Forge World resin model')}

<p>The tiniest Titan, the Warhound Titan is the beginner entry point for Titan collecting, if you consider $695 a reasonable entry point. In all honesty, this ranks as the least interesting-looking Titan on the list, being neither much of a looker nor particularly interesting rules-wise. Compare its weapons and rules to <a href="/products/imperial-knight-preceptor-canis-rex/">Canis Rex</a> and you are left a bit disappointed. Your $695 entry doesn't even include its arms! Each one is going to cost you $87 extra. If you're going to be spending big, you might as well get one of the next few models.</p>

<h2>#6 Acastus Knight Porphyrion</h2>

{stat_card('$710', 'Height', '10 in / 240 mm', '126', '700 pts',
           'https://wahapedia.ru/wh40k10ed/factions/imperial-knights/Acastus-Knight-Porphyrion')}

{model_img('acastus-knight-porphyrion.jpeg', 'Acastus Knight Porphyrion Forge World resin model')}

<p>The biggest and most heavily armored of the Imperial Knights, equipped with Strength 18 D6+6 damage twin-linked heavy lascannons, making it an absolute terror to mid-sized vehicles anywhere on the board. If you keep it stationary (with a 72-inch range, very possible) you also get lethal hits, making it nearly impossible for anything to survive this giant. I can imagine a few Tau Riptides and a Porphyrion trading shots across the table. That would be absolutely glorious carnage.</p>

<h2>#5 Legion Thunderhawk Gunship</h2>

{stat_card('$950', 'Length', '1.6 ft / 480 mm', '112', '840 pts',
           'https://wahapedia.ru/wh40k10ed/factions/space-marines/Thunderhawk-Gunship')}

{model_img('thunderhawk-gunship.jpeg', 'Legion Thunderhawk Gunship Forge World resin model')}

<p>A cheaper version (both in real-life cash and in-game points) than our #3 model, the Legion Thunderhawk Gunship is a stone-cold classic Space Marine model. <a href="https://www.polygon.com/tabletop-games/22698200/warhammer-40000-thunderhawk-gunship-auction-price-2021/" target="_blank" rel="noopener noreferrer">Its 1997 metal release fetched $35,000 at auction!</a> This beloved transport is one of the few actually usable in-game models on the list. Its 4 Twin Lascannons alongside the ability to transport 55 Space Marines makes it a shoe-in for some epic moments on the table. While I wouldn't recommend any of these models outright, the Legion Thunderhawk is probably one of the few Forge World models I would consider buying if I had the money to burn.</p>

<h2>#4 Mars Pattern Reaver Titan</h2>

{stat_card('$1,040', 'Height', '1.31 ft / 400 mm', '190', '2,200 pts',
           'https://wahapedia.ru/wh40k10ed/factions/adeptus-titanicus/Reaver-Titan')}

{model_img('reaver-titan.jpeg', 'Mars Pattern Reaver Titan Forge World resin model')}

<p>Our first $1,000+ model on the list, the Reaver Titan does not come with its carapace weapons or arms, which are sold separately for $130+. This model may be smaller than our #2 and #3 models but has more components to put together, making it a serious hobby challenge. Expect dozens of hours of work assembling and painting this centerpiece model. Looks-wise, this is an upgrade over the Warhound Titan.</p>

<h2>#3 Legion Sokar Stormbird</h2>

{stat_card('$1,580', 'Length', '1.64 ft / 500 mm', '147', '900 pts',
           'https://wahapedia.ru/wh40k10ed/factions/death-guard/Sokar-pattern-Stormbird')}

{model_img('sokar-stormbird.jpeg', 'Legion Sokar Stormbird Forge World resin model')}

<p>How many turrets and missiles do you need on a transport? If you said anything below a dozen, you are not a true Warhammer player. The Stormbird has 13 combined turrets and missiles to blast your enemies, plus room to house up to 55 Space Marines. In my opinion, I much prefer the Thunderhawk Gunship over this model. The Thunderhawk Gunship is a non-Legends model (playable on all tables) and puts this one to shame in the looks department.</p>

<h2>#2 Mars Pattern Warlord Titan Body</h2>

{stat_card('$1,955', 'Height', '1.97 ft / 600 mm', '156', '3,500 pts',
           'https://wahapedia.ru/wh40k10ed/factions/adeptus-titanicus/Warlord-Titan')}

{model_img('warlord-titan.jpeg', 'Mars Pattern Warlord Titan Body Forge World resin model')}

<p>The most ancient and superior Warlord Titan, the Mars Pattern Warlord Titan is a behemoth of a model standing nearly 2 feet tall with 156 individual components. Stack two <a href="/products/ork-stompa/">Ork Stompas</a> on top of each other and you have the height of this model.</p>

<p>This kit does not include the head, shoulder-mounted weapons, or arm options. These add-ons cost anywhere between $132 and $240 individually. You could buy an entire <a href="/products/cerastus-knight-lancer/">Cerastus Knight Lancer</a> for the price of a single weapon for this model. An entire 40K army can be bought from Games Workshop directly for the price of this model.</p>

<p>On the tabletop, I want to highlight its 100 wounds and its Striding Colossus ability: each time you target this model with a stratagem, you must spend 4x the CP cost to do so. An absolutely insane rule befitting Warhammer's most iconic Titan!</p>

<h2>#1 Manta</h2>

{stat_card('$2,080', 'Length', '2.08 ft / 630 mm, 2.8 ft wingspan, 28 lbs', '738 (320 resin, 418 plastic)', '2,100 pts',
           'https://wahapedia.ru/wh40k10ed/factions/t-au-empire/Manta')}

{model_img('manta.jpeg', 'Tau Manta Forge World resin model')}

<p>Technically, if you include the cost of weapons for the Warlord Titan, the Manta would be the second most expensive model. However, in terms of entry price, the Manta is the most expensive Warhammer 40K model and likely the world's most expensive commercially produced miniature. 28 pounds of plastic and resin with 738 individual components, the Manta is oddly the best bang for your buck in terms of hobbying. <a href="https://www.reddit.com/r/Tau40K/comments/19dz11n/week_4_and_she_is_all_built_manta_can_fly_now/" target="_blank" rel="noopener noreferrer">One Reddit user took 4 weeks just to get the Manta assembled</a>, not including painting. The Manta isn't just a hobby project, it's your hobby project for at least the next few months.</p>

<p>The profile for the Manta is just nuts. Two Strength 26 Heavy Rail Cannons dealing flat 12 damage, with 10 seeker missiles, the Manta is a delete button when supported by fellow T'au units. Add the 200-infantry capacity and 3D6 Deadly Demise and you have one of the craziest models in all of Warhammer 40K. Sadly, its 2,100 points total makes it not playable in a standard Warhammer 40K game. My 2026 Warhammer goal is to get a game played against a Manta and experience that cinematic moment of destroying it and watching it explode!</p>

{YOUTUBE_EMBED}

<h2>Where to Buy</h2>

<p>These epic-sized models go in and out of stock on the Warhammer website, so you need to be patient to get your hands on one. You can also find these models sold at a premium on eBay. If you are considering buying one of these epic-sized models, I would recommend buying it unassembled. The charm and fun of these models is the journey of assembling and painting them. While they are collector's items, I would recommend fielding them on the tabletop and giving you and your opponent an unforgettable and unique experience.</p>

<h2>Who Should Buy These Models?</h2>

<p>If you are an experienced painter and assembler, these models offer the perfect opportunity to test your skills and make an excellent centerpiece for your hobby room. If you are new to Warhammer and model assembly, <strong>DO NOT start with these as your first models.</strong> Stick to <a href="/blog/best-starter-warhammer-40k-armies-2026/">starter armies</a> that give you the freedom to make mistakes. Plastic models are far easier to assemble and paint than resin. Resin requires more work to remove imperfections and can often be brittle, causing pieces to break far more easily. There is also the risk of the resin warping, requiring special treatments to fix.</p>

<p>There is a reason Forge World models are often criticized by the community: they are expensive and difficult to work with. Proceed at your own risk, and if you go down this route, watch assembly guides from experienced hobbyists before starting your project.</p>
"""


class Command(BaseCommand):
    """Publish the Largest & Most Expensive Warhammer 40K Models Part 1 post (idempotent)."""

    help = 'Publishes the Most Expensive & Largest Warhammer 40K Models (Forge World Resin) blog post.'

    def add_arguments(self, parser):
        """Register CLI arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the blog post."""
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(f'Post already exists (pk={existing.pk}) -- skipping.')
            )
            return

        defaults = dict(
            slug=SLUG,
            title='The Largest & Most Expensive Warhammer 40K Models Currently Available: Part 1, Forge World Resin',
            excerpt=(
                'From the $535 Hierophant Bio-Titan to the $2,080 Tau Manta, we rank and review '
                'the 10 largest and most expensive Forge World resin models currently available '
                'in Warhammer 40K, including price, size, components, and in-game rules.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            featured_image_url='https://img.youtube.com/vi/SHg0RKppwEM/maxresdefault.jpg',
            featured_image_alt='Most Expensive Warhammer 40K Models: Warlord Titan vs Tau Manta',
            meta_title='Most Expensive Warhammer 40K Models: Forge World Resin Top 10',
            meta_description=(
                'From the $535 Hierophant Bio-Titan to the $2,080 Tau Manta, we rank the 10 '
                'largest and most expensive Forge World resin models in Warhammer 40K.'
            ),
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            post = existing
            self.stdout.write(
                self.style.SUCCESS(f'Updated existing post (pk={post.pk}, slug={post.slug}).')
            )
        else:
            post = Post(**defaults)
            post.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created post (pk={post.pk}, slug={post.slug}).')
            )

        tag_names = ['Forge World', 'Warhammer 40K', 'Pricing', 'Titans', 'Collector']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags attached: {tag_names}'))
