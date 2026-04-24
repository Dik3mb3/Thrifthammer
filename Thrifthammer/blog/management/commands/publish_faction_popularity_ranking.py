"""
Management command: publish_faction_popularity_ranking

Creates the 'Most Popular Warhammer 40K Factions Ranked by Their Digital
Footprint' blog post. Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_faction_popularity_ranking
    python manage.py publish_faction_popularity_ranking --force
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'warhammer-40k-faction-popularity-ranking'

BODY = """\
<p class="post-lead">Faction popularity is what drives Games Workshop decision making. It impacts new models, range refreshes, time spent on rules, lore, and all decisions impacting our community.</p>

<p>What if we could actually measure which Warhammer 40K factions are the most popular?</p>

<p>Unfortunately, that's not something we can answer with certainty, at least not without Games Workshop opening their books to us. But that doesn't mean we are completely in the dark.</p>

<p>I've made an honest attempt to answer that question by digging through the internet, tracking the popularity of Warhammer 40K factions across multiple internet platforms.</p>

<p>Welcome to my deep dive into the popularity of Warhammer factions.</p>

<p>Using data from social media and competitive play, we can build a surprisingly strong approximation of each faction's popularity by analyzing each army's digital footprint. Using this data we can isolate the most popular faction and the factions that are lagging behind.</p>

<h2>The Problem with Measuring Warhammer Faction Popularity</h2>

<p>Before diving into the data, we need to acknowledge that this isn't an exact science.</p>

<ul>
  <li>There is no official "faction popularity" dataset</li>
  <li>Sales data is proprietary</li>
  <li>Tournament data is skewed by meta shifts</li>
  <li>Social media metrics can be misleading</li>
</ul>

<p>So instead of relying on one source, I combined multiple ranking criteria together.</p>

<h2>Data Sources Used</h2>

<p>Each faction was ranked across three key categories:</p>
<ul>
  <li>Largest faction Reddit community</li>
  <li>Number of faction hashtags on Instagram</li>
  <li>Tournament representation over the last 2 years (to normalize for shifts in the meta)</li>
</ul>

<p>I then averaged each faction's ranking across these categories to create an overall "popularity score."</p>

<h2>Methodology: How the Data Was Collected</h2>

<h3>Reddit Communities</h3>
<ul>
  <li>Ranked by number of weekly visitors (as of April 2026)</li>
  <li>Tie-breaker: weekly post contributions</li>
</ul>
<p>Why I chose this criteria: Reddit represents some of the most engaged Warhammer fans. All types of community members are included from those who discuss lore, hobbying, and gameplay.</p>

<h3>Instagram Hashtags</h3>
<ul>
  <li>Ranked by total hashtag volume per faction (as of April 2026)</li>
  <li>The top 2 tags were combined as many factions have two common names (e.g. Astra Militarum + Imperial Guard, Adeptus Custodes + Custodes)</li>
</ul>
<p>Why I chose this criteria: Instagram captures volume. As one of the largest social platforms in the world it includes both casual and hardcore fans. This is a great gauge for each faction's cultural relevance and how actively it's discussed outside of hardcore communities.</p>

<h3>Tournament Representation</h3>
<ul>
  <li>Based on average player count per faction over the last 8 quarters (2024 to 2026)</li>
  <li>Data normalized to reduce the impact of shifts in the meta on the final ranking</li>
</ul>
<p>Why I chose this criteria: This is the most concrete signal of what actually hits the tabletop. While not perfect, it's the most measurable real-world engagement metric for gameplay. Those who play in tournaments are often Games Workshop's most engaged customers as they routinely buy models to keep up with in game changes.</p>

<h2>Warhammer 40K Faction Popularity Ranking</h2>

<style>
#fpr-wrap {
  overflow-x: auto;
  margin: var(--sp-6, 1.5rem) 0;
}
#fpr-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
  background: var(--bg-card, #1a1b1c);
  border: 1px solid var(--border-subtle, rgba(255,255,255,0.08));
  border-radius: 6px;
  overflow: hidden;
}
#fpr-table thead th {
  background: #9a6e10;
  color: #fff;
  padding: 0.6rem 0.75rem;
  text-align: left;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  border-bottom: 2px solid var(--border-subtle, rgba(255,255,255,0.12));
}
#fpr-table thead th[data-sort] {
  cursor: pointer;
  user-select: none;
}
#fpr-table thead th[data-sort]:hover {
  background: #b07e18;
}
.fpr-arrow {
  display: inline-block;
  margin-left: 0.3rem;
  font-size: 0.7rem;
  opacity: 0.7;
}
#fpr-table tbody tr {
  border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.06));
  transition: background 0.1s;
}
#fpr-table tbody tr:last-child {
  border-bottom: none;
}
#fpr-table tbody tr:nth-child(even) {
  background: rgba(255,255,255,0.03);
}
#fpr-table tbody tr:hover {
  background: rgba(200,146,26,0.08);
}
#fpr-table td {
  padding: 0.55rem 0.75rem;
  vertical-align: middle;
  color: var(--text-primary, #e8e8e8);
}
.fpr-rank {
  font-weight: 700;
  font-size: 0.9rem;
  display: inline-block;
  width: 1.8rem;
  text-align: center;
}
.fpr-rank-gold   { color: #c8921a; }
.fpr-rank-silver { color: #a0a0a0; }
.fpr-rank-bronze { color: #a0522d; }
.fpr-rank-low    { color: var(--text-muted, #777); }
#fpr-table td a {
  color: var(--accent-gold-lt, #d4a832);
  text-decoration: none;
  font-weight: 600;
}
#fpr-table td a:hover {
  text-decoration: underline;
}
.fpr-num {
  text-align: center;
  color: var(--text-muted, #888);
}
</style>

<div id="fpr-wrap">
  <table id="fpr-table">
    <thead>
      <tr>
        <th data-sort="0">Rank <span class="fpr-arrow">▲</span></th>
        <th>Faction</th>
        <th data-sort="2">Tournament <span class="fpr-arrow">⇅</span></th>
        <th data-sort="3">Instagram <span class="fpr-arrow">⇅</span></th>
        <th data-sort="4">Reddit <span class="fpr-arrow">⇅</span></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="fpr-rank fpr-rank-gold" data-val="1">1</span></td>
        <td><a href="/factions/space-marines/">Space Marines</a></td>
        <td class="fpr-num" data-val="1">1</td>
        <td class="fpr-num" data-val="1">1</td>
        <td class="fpr-num" data-val="2">2</td>
      </tr>
      <tr>
        <td><span class="fpr-rank fpr-rank-silver" data-val="2">2</span></td>
        <td><a href="/factions/astra-militarum/">Astra Militarum</a></td>
        <td class="fpr-num" data-val="4">4</td>
        <td class="fpr-num" data-val="4">4</td>
        <td class="fpr-num" data-val="3">3</td>
      </tr>
      <tr>
        <td><span class="fpr-rank fpr-rank-bronze" data-val="3">3</span></td>
        <td><a href="/factions/tyranids/">Tyranids</a></td>
        <td class="fpr-num" data-val="5">5</td>
        <td class="fpr-num" data-val="11">11</td>
        <td class="fpr-num" data-val="1">1</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="4">4</span></td>
        <td><a href="/factions/orks/">Orks</a></td>
        <td class="fpr-num" data-val="10">10</td>
        <td class="fpr-num" data-val="3">3</td>
        <td class="fpr-num" data-val="4">4</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="5">5</span></td>
        <td><a href="/factions/necrons/">Necrons</a></td>
        <td class="fpr-num" data-val="2">2</td>
        <td class="fpr-num" data-val="10">10</td>
        <td class="fpr-num" data-val="7">7</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="6">6</span></td>
        <td><a href="/factions/chaos-space-marines/">Chaos Space Marines</a></td>
        <td class="fpr-num" data-val="9">9</td>
        <td class="fpr-num" data-val="6">6</td>
        <td class="fpr-num" data-val="5">5</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="7">7</span></td>
        <td><a href="/factions/tau-empire/">T'au Empire</a></td>
        <td class="fpr-num" data-val="12">12</td>
        <td class="fpr-num" data-val="2">2</td>
        <td class="fpr-num" data-val="6">6</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="8">8</span></td>
        <td><a href="/factions/death-guard/">Death Guard</a></td>
        <td class="fpr-num" data-val="3">3</td>
        <td class="fpr-num" data-val="7">7</td>
        <td class="fpr-num" data-val="11">11</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="9">9</span></td>
        <td><a href="/factions/blood-angels/">Blood Angels</a></td>
        <td class="fpr-num" data-val="11">11</td>
        <td class="fpr-num" data-val="8">8</td>
        <td class="fpr-num" data-val="9">9</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="10">10</span></td>
        <td><a href="/factions/aeldari/">Aeldari</a></td>
        <td class="fpr-num" data-val="6">6</td>
        <td class="fpr-num" data-val="9">9</td>
        <td class="fpr-num" data-val="14">14</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="11">11</span></td>
        <td><a href="/factions/dark-angels/">Dark Angels</a></td>
        <td class="fpr-num" data-val="16">16</td>
        <td class="fpr-num" data-val="5">5</td>
        <td class="fpr-num" data-val="10">10</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="12">12</span></td>
        <td><a href="/factions/custodes/">Adeptus Custodes</a></td>
        <td class="fpr-num" data-val="8">8</td>
        <td class="fpr-num" data-val="18">18</td>
        <td class="fpr-num" data-val="8">8</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="13">13</span></td>
        <td><a href="/factions/world-eaters/">World Eaters</a></td>
        <td class="fpr-num" data-val="7">7</td>
        <td class="fpr-num" data-val="19">19</td>
        <td class="fpr-num" data-val="17">17</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="14">14</span></td>
        <td><a href="/factions/sisters-of-battle/">Adepta Sororitas</a></td>
        <td class="fpr-num" data-val="21">21</td>
        <td class="fpr-num" data-val="13">13</td>
        <td class="fpr-num" data-val="13">13</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="15">15</span></td>
        <td><a href="/factions/black-templars/">Black Templars</a></td>
        <td class="fpr-num" data-val="24">24</td>
        <td class="fpr-num" data-val="15">15</td>
        <td class="fpr-num" data-val="12">12</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="16">16</span></td>
        <td><a href="/factions/imperial-knights/">Imperial Knights</a></td>
        <td class="fpr-num" data-val="13">13</td>
        <td class="fpr-num" data-val="22">22</td>
        <td class="fpr-num" data-val="18">18</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="17">17</span></td>
        <td><a href="/factions/space-wolves/">Space Wolves</a></td>
        <td class="fpr-num" data-val="22">22</td>
        <td class="fpr-num" data-val="12">12</td>
        <td class="fpr-num" data-val="20">20</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="18">18</span></td>
        <td><a href="/factions/adeptus-mechanicus/">Adeptus Mechanicus</a></td>
        <td class="fpr-num" data-val="25">25</td>
        <td class="fpr-num" data-val="14">14</td>
        <td class="fpr-num" data-val="16">16</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="19">19</span></td>
        <td><a href="/factions/emperors-children/">Emperor's Children</a></td>
        <td class="fpr-num" data-val="17">17</td>
        <td class="fpr-num" data-val="25">25</td>
        <td class="fpr-num" data-val="15">15</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="20">20</span></td>
        <td><a href="/factions/thousand-sons/">Thousand Sons</a></td>
        <td class="fpr-num" data-val="18">18</td>
        <td class="fpr-num" data-val="20">20</td>
        <td class="fpr-num" data-val="19">19</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="21">21</span></td>
        <td><a href="/factions/drukhari/">Drukhari</a></td>
        <td class="fpr-num" data-val="23">23</td>
        <td class="fpr-num" data-val="17">17</td>
        <td class="fpr-num" data-val="22">22</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="22">22</span></td>
        <td>Chaos Daemons</td>
        <td class="fpr-num" data-val="14">14</td>
        <td class="fpr-num" data-val="21">21</td>
        <td class="fpr-num" data-val="28">28</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="23">23</span></td>
        <td><a href="/factions/chaos-knights/">Chaos Knights</a></td>
        <td class="fpr-num" data-val="15">15</td>
        <td class="fpr-num" data-val="26">26</td>
        <td class="fpr-num" data-val="24">24</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="24">24</span></td>
        <td><a href="/factions/leagues-of-votann/">Leagues of Votann</a></td>
        <td class="fpr-num" data-val="19">19</td>
        <td class="fpr-num" data-val="27">27</td>
        <td class="fpr-num" data-val="21">21</td>
      </tr>
      <tr>
        <td><span class="fpr-rank" data-val="25">25</span></td>
        <td><a href="/factions/grey-knights/">Grey Knights</a></td>
        <td class="fpr-num" data-val="20">20</td>
        <td class="fpr-num" data-val="24">24</td>
        <td class="fpr-num" data-val="23">23</td>
      </tr>
      <tr>
        <td><span class="fpr-rank fpr-rank-low" data-val="26">26</span></td>
        <td><a href="/factions/deathwatch/">Deathwatch</a></td>
        <td class="fpr-num" data-val="27">27</td>
        <td class="fpr-num" data-val="16">16</td>
        <td class="fpr-num" data-val="26">26</td>
      </tr>
      <tr>
        <td><span class="fpr-rank fpr-rank-low" data-val="27">27</span></td>
        <td><a href="/factions/genestealer-cults/">Genestealer Cults</a></td>
        <td class="fpr-num" data-val="26">26</td>
        <td class="fpr-num" data-val="23">23</td>
        <td class="fpr-num" data-val="25">25</td>
      </tr>
      <tr>
        <td><span class="fpr-rank fpr-rank-low" data-val="28">28</span></td>
        <td>Imperial Agents</td>
        <td class="fpr-num" data-val="28">28</td>
        <td class="fpr-num" data-val="28">28</td>
        <td class="fpr-num" data-val="27">27</td>
      </tr>
    </tbody>
  </table>
</div>

<script>
(function () {
  var table = document.getElementById('fpr-table');
  if (!table) return;
  var tbody = table.querySelector('tbody');
  var headers = Array.from(table.querySelectorAll('thead th[data-sort]'));
  var currentSortIdx = 0;
  var ascending = true;

  function getVal(row, colIndex) {
    var cell = row.cells[colIndex];
    var span = cell.querySelector('[data-val]');
    if (span) return parseInt(span.getAttribute('data-val'), 10);
    return parseInt(cell.getAttribute('data-val'), 10) || 0;
  }

  function updateArrows(activeIdx) {
    headers.forEach(function (th) {
      var arrow = th.querySelector('.fpr-arrow');
      if (!arrow) return;
      var idx = parseInt(th.getAttribute('data-sort'), 10);
      if (idx === activeIdx) {
        arrow.textContent = ascending ? '\u25b2' : '\u25bc';
        arrow.style.opacity = '1';
      } else {
        arrow.textContent = '\u21c5';
        arrow.style.opacity = '0.5';
      }
    });
  }

  function sortBy(colIndex) {
    var rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort(function (a, b) {
      var diff = getVal(a, colIndex) - getVal(b, colIndex);
      return ascending ? diff : -diff;
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
    updateArrows(colIndex);
  }

  headers.forEach(function (th) {
    th.addEventListener('click', function () {
      var colIndex = parseInt(th.getAttribute('data-sort'), 10);
      if (currentSortIdx === colIndex) {
        ascending = !ascending;
      } else {
        currentSortIdx = colIndex;
        ascending = true;
      }
      sortBy(colIndex);
    });
  });
})();
</script>

<h2>Key Takeaways</h2>

<h3>Unsurprising Results</h3>

<p><strong>Space Marines rank #1 across almost every metric except Reddit.</strong></p>
<ul>
  <li>Likely due to fragmented communities across chapters</li>
</ul>

<p><strong>Imperial Agents sit at the bottom.</strong></p>
<ul>
  <li>New army, weak rules, and low synergy across units equals low popularity</li>
</ul>

<p><strong>Expensive or outdated factions lag behind.</strong></p>
<ul>
  <li>Entry cost and updated model range clearly impact popularity. If Games Workshop ignores your faction it's an uphill battle to maintain strong popularity.</li>
</ul>

<p><strong>Games Workshop's attempted removal of Deathwatch and Chaos Daemons makes sense when looking at this data.</strong></p>
<ul>
  <li>Lack of widespread popularity has led to underinvestment from Games Workshop into these factions, which makes new and existing players hesitant to invest their money and time into the faction.</li>
</ul>

<h3>Surprising Results</h3>

<p><strong>5 of the Top 10 factions are Xenos.</strong></p>
<ul>
  <li>A big shift from the narrative that only Imperium related factions drive sales. Xenos are clearly a big sales driver for Games Workshop, likely why the last few launch boxes have featured a Xenos faction.</li>
</ul>

<p><strong>T'au Empire ranks surprisingly high (#7).</strong></p>
<ul>
  <li>Despite historical community backlash, being a monophase army, and their non-grimdark aesthetic, their popularity has been consistently high.</li>
</ul>

<p><strong>Knights underperformed my expectations.</strong></p>
<ul>
  <li>As a centerpiece army with the ability to ally across other factions, I expected them to rank higher.</li>
</ul>

<p><strong>Chaos faction popularity is wildly inconsistent. Games Workshop has work to do in bridging the gap between these factions.</strong></p>
<ul>
  <li>Top-tier: Chaos Space Marines, Death Guard</li>
  <li>Mid: World Eaters</li>
  <li>Low: Thousand Sons, Emperor's Children</li>
</ul>

<h3>Other Interesting Data Points</h3>

<ul>
  <li>Space Marines have 2M+ Instagram hashtags (3x the next closest faction)</li>
  <li>T'au subreddit remained Top 6 from 2021 to 2026, showing major staying power as a 40K faction</li>
  <li>Harlequins (not in dataset) Reddit community was the only one to decline in weekly visitors from 2021. Shows that losing standalone faction support has a massive impact on overall popularity.</li>
  <li>Video game communities (e.g., Space Marine 2) were excluded from this data set but have significantly larger communities than traditional Warhammer communities</li>
</ul>

<p>Most "hardcore" Reddit communities (measured by weekly posts as a percentage of total visitors per week) as of April 2026 are:</p>
<ol>
  <li>Orks</li>
  <li>Imperial Knights</li>
  <li>World Eaters</li>
</ol>

<h2>Top 5 Most Popular Warhammer 40K Factions: The Why?</h2>

<h3><a href="/factions/space-marines/">Space Marines</a></h3>
<ul>
  <li>Poster boys of the entire universe, Space Marines are built to be popular</li>
  <li>Easy to paint makes them photogenic on platforms like Instagram</li>
  <li>Most lore and non-tabletop content is focused on them, making them most people's first (and sometimes only) entry point to the hobby</li>
</ul>

<h3><a href="/factions/astra-militarum/">Astra Militarum</a></h3>
<ul>
  <li>Lore is arguably the strongest, with Gaunt's Ghosts being recommended to me a million times by guard players</li>
  <li>World War 2 motif captures traditional wargamers and those who love that aesthetic</li>
  <li>Army has great unit variety and playstyles</li>
</ul>

<h3><a href="/factions/tyranids/">Tyranids</a></h3>
<ul>
  <li>10th edition launch box popularized Tyranids with a nice entry point into the army</li>
  <li>Army gives players the choice of "Monster Mash" lists, horde style lists, or mixed ranks making it a good all-rounder army for new players</li>
  <li>Has an aesthetic that a majority of Warhammer players enjoy</li>
</ul>

<h3><a href="/factions/orks/">Orks</a></h3>
<ul>
  <li>High volume, high variance dice rolls is attractive to players who want to chuck a ton of dice per game</li>
  <li>A kitbasher's dream army, Orks' aesthetic and motif allows for creative reimagining of how units can look</li>
  <li>The "comedic relief" of Warhammer, Orks are a laid-back fun way to approach a serious setting</li>
</ul>

<h3><a href="/factions/necrons/">Necrons</a></h3>
<ul>
  <li>Consistently competitive and very beginner friendly faction gameplay wise</li>
  <li>Influx of new models and lore has helped push Necron popularity</li>
  <li>Easiest army to paint and hobby, with a nice mix of centerpieces with standard units</li>
</ul>

<h2>Top 5 Least Popular Warhammer 40K Factions: The Why?</h2>

<h3>Imperial Agents</h3>
<ul>
  <li>New faction with weak rules and synergy has dried up most interest in the faction</li>
  <li>Treated as a sales channel for those who own Imperium allies to run them as a separate army, leading to purchases of expensive kits that aren't worth a ton of in-game points</li>
  <li>No long-term direction. Will this faction exist in future editions past 11th? What do Imperial Agents actually do in-game that is different?</li>
</ul>

<h3><a href="/factions/genestealer-cults/">Genestealer Cults</a></h3>
<ul>
  <li>One of the most expensive armies in terms of cost to start</li>
  <li>Historically complex rules that are often reworked, creating an army that swings from worst to best at Games Workshop's whim</li>
  <li>A massive hobby project (high volume of small units), with no unique centerpiece models</li>
</ul>

<h3><a href="/factions/deathwatch/">Deathwatch</a></h3>
<ul>
  <li>A "zombie" faction that was already killed by Games Workshop, brought back by protests from the community</li>
  <li>A mismatch of Space Marine units, with technical rules that don't appeal to the majority of tabletop players</li>
  <li>No long-term direction for the faction</li>
</ul>

<h3><a href="/factions/grey-knights/">Grey Knights</a></h3>
<ul>
  <li>Models are outdated and the faction's centerpiece the Nemesis Dreadknight is one of the worst designed models in Warhammer 40K</li>
  <li>Lore has not been treated as well as other Space Marine factions</li>
  <li>The death of the psychic phase has eliminated a ton of passion for the army gameplay wise</li>
</ul>

<h3><a href="/factions/leagues-of-votann/">Leagues of Votann</a></h3>
<ul>
  <li>Suffers from being a relatively new faction (yes I know squats existed before)</li>
  <li>Games Workshop has not nailed the army's gimmick yet, switching army rules in the quest to find the right one</li>
  <li>Lacks a full range and enough lore to inspire more love across the community</li>
</ul>

<h2>Predicting Faction Popularity</h2>

<p>I think it's fun to speculate about which factions might rise and fall in popularity in the next 10 years. Here are my opinions.</p>

<h3>Risers</h3>

<p><strong><a href="/factions/leagues-of-votann/">Leagues of Votann</a>:</strong> Xenos are popular in general, and Dwarves are an extremely popular fantasy race. If/when Games Workshop decides to expand the range and lore I believe Leagues of Votann will be in the top half of factions in popularity.</p>

<p><strong><a href="/factions/emperors-children/">Emperor's Children</a>:</strong> Early results have been good! For a faction that recently got relaunched they have been extremely popular. Their range is tiny; adding a few more units could catapult this faction up the rankings. The colorful color schemes you can do for EC are perfect for Instagram and social media consumption.</p>

<p><strong><a href="/factions/grey-knights/">Grey Knights</a>:</strong> This inclusion is simply because things can't get worse for Grey Knights. A range refresh (which will definitely happen in the next 10 years) is an easy boost to their popularity. They also remain one of the cheapest armies in the game, a huge selling point to new players and those looking to expand to another army. Refreshes also bring new lore, which would be massive for Grey Knight popularity.</p>

<h3>Fallers</h3>

<p><strong><a href="/factions/drukhari/">Drukhari</a>:</strong> Even with the recent model refresh the range continues to shrink and support for the faction has dried up from Games Workshop. I can easily see Games Workshop absorbing them into Eldar. Difficult to play with an aesthetic that doesn't appeal to most people (I like it). Drukhari I think will continue to fall.</p>

<p><strong>Chaos Daemons:</strong> The future for Chaos Daemons remains grim. They might be dead as a standalone faction with each of the mortal legions absorbing parts of their range. While an index might be created to keep them alive, their remaining popularity may be split across the different chaos factions.</p>

<p><strong><a href="/factions/death-guard/">Death Guard</a>:</strong> Death Guard won't ever be unpopular but they have been spoiled by Games Workshop compared to other chaos factions. It's reasonable to expect that the other chaos factions will receive improved ranges in the next decade and become more attractive to newer players over time. I don't think there are actually more Death Guard fans in the world than Thousand Sons, World Eaters, or Emperor's Children. It's just that there are more Death Guard out in the marketplace.</p>

<h2>The Space Marine Problem</h2>

<p>Before we conclude the article I wanted to discuss the issues with judging Space Marine popularity. Any analysis of Space Marine faction popularity runs into major issues:</p>

<h3>1. Fragmentation</h3>
<ul>
  <li>Space Marines are split across countless chapters and communities</li>
  <li>Their true popularity is likely significantly underestimated without including every niche community and non-tabletop community</li>
</ul>

<h3>2. Competitive Distortion</h3>
<ul>
  <li>Players often switch between Marine chapters based on the meta</li>
  <li>It's very easy for players to shift between Space Marine armies, potentially impacting the popularity of specific Marine chapters. Why would a competitive player play the worst Space Marine chapter when you can play the strongest with little hobbying effort?</li>
</ul>

<h3>3. Missing Data: Video Games and Lore</h3>
<ul>
  <li>Major titles like Space Marine 2 and Rogue Trader were excluded, titles that have larger online communities than tabletop</li>
  <li>Video games and lore channels (books, YouTube, etc.) act as funnels to the tabletop game and thus are good indicators of current and future popularity</li>
</ul>

<h3>4. The Casual Player Base</h3>
<ul>
  <li>Many Space Marine players don't use Reddit or post on social media and don't play more than a few times per year</li>
  <li>Difficult to capture this player base, but I am certain that if they were included the popularity disparity between Space Marines and other factions would be even greater</li>
</ul>

<h2>Final Thoughts</h2>

<p>Popularity in Warhammer 40K isn't just about what people play on the tabletop. It's about what they engage with.</p>

<p>By combining Reddit, Instagram, and tournament data, we get a strong approximation of faction popularity and cultural relevance. This analysis is not perfect, but it's an honest attempt to gauge popularity through multiple community perspectives.</p>

<p>There is one data point you can't argue against: Space Marines will always be the most popular faction in Warhammer 40K.</p>
"""


class Command(BaseCommand):
    """Publish the Warhammer 40K Faction Popularity Ranking blog post."""

    help = 'Publishes the faction popularity ranking post (idempotent).'

    def add_arguments(self, parser):
        """Add optional --force flag to overwrite an existing post."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
        )

    def handle(self, *args, **options):
        """Create or update the faction popularity ranking post."""
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()

        if existing and not options['force']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Post already exists (pk={existing.pk}) — skipping. '
                    f'Use --force to overwrite.'
                )
            )
            return

        defaults = dict(
            title='Most Popular Warhammer 40K Factions Ranked by Their Digital Footprint',
            slug=SLUG,
            excerpt=(
                'We ranked all 28 Warhammer 40K factions using Reddit, Instagram, and '
                'tournament data to measure each army\'s digital footprint. '
                'Find out which factions are truly the most popular.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            meta_title='Most Popular Warhammer 40K Factions Ranked (2026 Data)',
            meta_description=(
                'We ranked all 28 Warhammer 40K factions using Reddit, Instagram, '
                'and tournament data. Space Marines lead, but 5 of the top 10 are Xenos.'
            ),
        )

        if existing:
            for attr, val in defaults.items():
                setattr(existing, attr, val)
            existing.save()
            post = existing
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated existing post (pk={post.pk}, slug={post.slug}).'
                )
            )
        else:
            post = Post(**defaults)
            post.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created post (pk={post.pk}, slug={post.slug}).'
                )
            )

        tag, _ = Tag.objects.get_or_create(
            name='Faction Breakdown',
            defaults={'slug': 'faction-breakdown'},
        )
        post.tags.set([tag])
        self.stdout.write(self.style.SUCCESS('Tag attached: Faction Breakdown'))
