"""
Management command: publish_economics_part1

Creates the 'Is Warhammer 40K Getting More Expensive? Part 1' blog post.
Safe to run multiple times (idempotent).

Usage:
    python manage.py publish_economics_part1
    python manage.py publish_economics_part1 --force  # overwrite existing
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

SLUG = 'warhammer-40k-launch-box-prices-economics-part-1'

# ── Reusable style helpers (inline, so no new CSS classes are needed) ────────
_CARD   = 'background:#1c2230;border-radius:10px;padding:1.25rem 1.5rem;margin:1.5rem 0;overflow-x:auto;'
_LEGEND = 'display:flex;gap:1.5rem;margin-bottom:1.25rem;font-size:0.75rem;font-family:Oswald,sans-serif;text-transform:uppercase;letter-spacing:0.06em;color:#7a8090;'
_SWATCH_GOLD    = 'display:inline-block;width:14px;height:3px;background:#c8922a;border-radius:2px;margin-right:4px;vertical-align:middle;'
_SWATCH_ADJ     = 'display:inline-block;width:14px;height:3px;background:rgba(240,192,96,0.3);border-radius:2px;margin-right:4px;vertical-align:middle;'
_ROW    = 'display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;'
_LABEL  = 'font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;'
_BARS   = 'display:flex;flex-direction:column;gap:3px;'
_VALS   = 'font-size:0.74rem;line-height:1.4;'

def _bar(launch_pct, adj_pct, currency, launch, adj):
    """Return HTML for a two-bar row (launch + inflation-adjusted)."""
    return (
        f'<div style="{_ROW}">'
        f'  <div style="{_LABEL}">{{}}</div>'
        f'  <div style="{_BARS}">'
        f'    <div style="height:9px;background:#c8922a;border-radius:3px;width:{launch_pct:.1f}%;"></div>'
        f'    <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:{adj_pct:.1f}%;"></div>'
        f'  </div>'
        f'  <div style="{_VALS}">'
        f'    <div style="color:#c8922a;font-weight:700;">{currency}{launch}</div>'
        f'    <div style="color:rgba(240,192,96,0.55);font-size:0.68rem;">{currency}{adj} adj</div>'
        f'  </div>'
        f'</div>'
    )


def _chg_style(val):
    """Return inline color style for a % change cell."""
    if val is None:
        return 'color:#5c6480;'
    if val < 0:
        return 'color:#4aab72;font-weight:600;'   # green — price fell in real terms
    if val >= 25:
        return 'color:#d44040;font-weight:600;'   # red — well above inflation
    return 'color:#f0c060;font-weight:600;'        # gold — moderate increase


def _pts_bar_color(pts):
    if pts >= 9.0:
        return '#4aab72'   # green — great value
    if pts >= 7.0:
        return '#c8922a'   # gold — decent
    return '#d44040'       # red — poor value per dollar


BODY = """\
<p>One of the most common discussions in the Warhammer 40K community is whether Warhammer is getting more expensive or if it always was expensive. Is Games Workshop just a greedy company squeezing players' wallets, or are price hikes over time simply a symptom of inflation, rising business costs, or increased product support?</p>

<p>Today, we won't answer all of these questions. Instead, let's start this journey by going back in time and looking at Warhammer 40K launch boxes from 2nd Edition through 10th Edition, comparing:</p>

<ul>
  <li>Launch price</li>
  <li>Release year</li>
  <li>Model counts</li>
  <li>Inflation-adjusted cost</li>
  <li>Important events</li>
</ul>

<p>This is Part 1 of a multi-part series analyzing Warhammer 40K economics and whether Games Workshop is unfairly maligned for their pricing practices.</p>

<h2>A Note on the Data</h2>

<p>Let's get the boring things out of the way:</p>

<ul>
  <li><strong>Inflation</strong> &mdash; the general increase in prices for goods and services over time. The idea that $100 in 2000 is not the same as $100 in 2026 as the cost for all products (including Warhammer) has gone up.</li>
  <li><strong>Inflation Adjustment</strong> &mdash; Comparing prices for each launch box in today's money helps compare prices at different points in time. Basically, if a 2nd Edition box launched today, what would be the expected price knowing what inflation was over the last 30 years?</li>
  <li><strong>Inflation Between Editions</strong> &mdash; The total increase in prices for goods and services for each edition's length of play. This metric compares price increases in each edition's launch box versus the general increase of other goods and services during the same time period.</li>
</ul>

<h2>The Big Picture: US Launch Box Prices Across Editions</h2>

<p style="font-size:0.82rem;color:var(--text-muted);margin-top:-0.5rem;">US inflation estimates sourced from <a href="https://www.usinflationcalculator.com/" target="_blank" rel="noopener">usinflationcalculator.com</a>. 2nd and 3rd Edition USD prices were estimated from community forums and Reddit threads based on exchange rates at the time.</p>

<!-- ── US PRICE BAR CHART ─────────────────────────────────────────────── -->
<div style="background:#1c2230;border-radius:10px;padding:1.25rem 1.5rem;margin:1.75rem 0;overflow-x:auto;">
  <div style="font-family:Oswald,sans-serif;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;color:#c8bfb0;margin-bottom:0.25rem;">Launch Box Price vs. 2026 Inflation-Adjusted Value (USD)</div>
  <div style="font-size:0.72rem;color:#5c6480;margin-bottom:1.1rem;">Bars show actual launch price (gold) and what inflation would suggest it should cost today (faint).</div>
  <div style="display:flex;gap:1.5rem;margin-bottom:1.1rem;">
    <span style="font-size:0.72rem;color:#7a8090;font-family:Oswald,sans-serif;text-transform:uppercase;letter-spacing:0.04em;display:flex;align-items:center;gap:5px;"><span style="display:inline-block;width:14px;height:3px;background:#c8922a;border-radius:2px;"></span>Launch Price</span>
    <span style="font-size:0.72rem;color:#7a8090;font-family:Oswald,sans-serif;text-transform:uppercase;letter-spacing:0.04em;display:flex;align-items:center;gap:5px;"><span style="display:inline-block;width:14px;height:3px;background:rgba(240,192,96,0.3);border-radius:2px;"></span>2026 Adjusted Value</span>
  </div>
  <div style="min-width:300px;">

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">2nd Ed &rsquo;93</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:22.4%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:50.7%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$60</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$136 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">3rd Ed &rsquo;98</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:33.6%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:67.2%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$90</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$180 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">4th Ed &rsquo;04</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:28.0%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:48.5%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$75</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$130 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">5th Ed &rsquo;08</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:28.0%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:42.5%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$75</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$114 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">6th Ed &rsquo;12</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:37.3%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:53.0%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$100</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$142 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">7th Ed &rsquo;14</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:41.0%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:56.7%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$110</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$152 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">8th Ed &rsquo;17</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:59.7%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:79.5%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$160</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$213 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">9th Ed &rsquo;20</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:74.6%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:94.4%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$200</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$253 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#c8bfb0;text-align:right;">10th Ed &rsquo;23</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:93.3%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:100%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">$250</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">$268 adj</div>
      </div>
    </div>

    <div style="height:1px;background:#2a2e3a;margin:0.75rem 0;"></div>
    <div style="display:grid;grid-template-columns:110px 1fr 115px;align-items:center;gap:0.5rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.72rem;text-transform:uppercase;color:#5c6480;text-align:right;">Total change</div>
      <div></div>
      <div style="font-size:0.72rem;line-height:1.4;color:#5c6480;">+97% adj &nbsp;|&nbsp; 111% inflation</div>
    </div>

  </div>
</div>

<!-- ── US DATA TABLE ──────────────────────────────────────────────────── -->
<table>
  <thead>
    <tr>
      <th>Edition</th>
      <th>Box Name</th>
      <th>Year</th>
      <th>Launch Price (USD)</th>
      <th>What That Price Is Worth in 2026 (USD)</th>
      <th>Price Change vs. Prior Edition (Inflation-Adjusted)</th>
      <th>Cumulative Inflation During Edition Lifespan</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>2nd Ed</strong></td>
      <td>2nd Edition Starter Box</td>
      <td>1993</td>
      <td>$60</td>
      <td>$136</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
    </tr>
    <tr>
      <td><strong>3rd Ed</strong></td>
      <td>3rd Edition Starter</td>
      <td>1998</td>
      <td>$90</td>
      <td>$180</td>
      <td style="color:#d44040;font-weight:600;">+32%</td>
      <td>13%</td>
    </tr>
    <tr>
      <td><strong>4th Ed</strong></td>
      <td>Battle for Macragge</td>
      <td>2004</td>
      <td>$75</td>
      <td>$130</td>
      <td style="color:#4aab72;font-weight:600;">&#8722;28%</td>
      <td>16%</td>
    </tr>
    <tr>
      <td><strong>5th Ed</strong></td>
      <td>Assault on Black Reach</td>
      <td>2008</td>
      <td>$75</td>
      <td>$114</td>
      <td style="color:#4aab72;font-weight:600;">&#8722;12%</td>
      <td>14%</td>
    </tr>
    <tr>
      <td><strong>6th Ed</strong></td>
      <td>Dark Vengeance</td>
      <td>2012</td>
      <td>$100</td>
      <td>$142</td>
      <td style="color:#d44040;font-weight:600;">+25%</td>
      <td>7%</td>
    </tr>
    <tr>
      <td><strong>7th Ed</strong></td>
      <td>Dark Vengeance</td>
      <td>2014</td>
      <td>$110</td>
      <td>$152</td>
      <td style="color:#f0c060;font-weight:600;">+7%</td>
      <td>3%</td>
    </tr>
    <tr>
      <td><strong>8th Ed</strong></td>
      <td>Dark Imperium</td>
      <td>2017</td>
      <td>$160</td>
      <td>$213</td>
      <td style="color:#d44040;font-weight:600;">+40%</td>
      <td>4%</td>
    </tr>
    <tr>
      <td><strong>9th Ed</strong></td>
      <td>Indomitus</td>
      <td>2020</td>
      <td>$200</td>
      <td>$253</td>
      <td style="color:#d44040;font-weight:600;">+19%</td>
      <td>6%</td>
    </tr>
    <tr>
      <td><strong>10th Ed</strong></td>
      <td>Leviathan</td>
      <td>2023</td>
      <td>$250</td>
      <td>$268</td>
      <td style="color:#f0c060;font-weight:600;">+6%</td>
      <td>18%</td>
    </tr>
    <tr style="border-top:1px solid #3a3e4a;">
      <td colspan="3" style="font-family:Oswald,sans-serif;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.04em;color:#7a8090;">Across All Editions</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#f0c060;font-weight:600;">+97%</td>
      <td>111%</td>
    </tr>
  </tbody>
</table>

<h2>The Big Picture: UK Launch Box Prices Across Editions</h2>

<p style="font-size:0.82rem;color:var(--text-muted);margin-top:-0.5rem;">UK inflation estimates sourced from the <a href="https://www.bankofengland.co.uk/monetary-policy/inflation/inflation-calculator" target="_blank" rel="noopener">Bank of England Inflation Calculator</a>.</p>

<!-- ── UK PRICE BAR CHART ─────────────────────────────────────────────── -->
<div style="background:#1c2230;border-radius:10px;padding:1.25rem 1.5rem;margin:1.75rem 0;overflow-x:auto;">
  <div style="font-family:Oswald,sans-serif;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;color:#c8bfb0;margin-bottom:0.25rem;">Launch Box Price vs. 2026 Inflation-Adjusted Value (GBP)</div>
  <div style="font-size:0.72rem;color:#5c6480;margin-bottom:1.1rem;">Bars show actual launch price (gold) and what inflation would suggest it should cost today (faint).</div>
  <div style="display:flex;gap:1.5rem;margin-bottom:1.1rem;">
    <span style="font-size:0.72rem;color:#7a8090;font-family:Oswald,sans-serif;text-transform:uppercase;letter-spacing:0.04em;display:flex;align-items:center;gap:5px;"><span style="display:inline-block;width:14px;height:3px;background:#c8922a;border-radius:2px;"></span>Launch Price</span>
    <span style="font-size:0.72rem;color:#7a8090;font-family:Oswald,sans-serif;text-transform:uppercase;letter-spacing:0.04em;display:flex;align-items:center;gap:5px;"><span style="display:inline-block;width:14px;height:3px;background:rgba(240,192,96,0.3);border-radius:2px;"></span>2026 Adjusted Value</span>
  </div>
  <div style="min-width:300px;">

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">2nd Ed &rsquo;93</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:21.7%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:47.2%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;34.99</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;76 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">3rd Ed &rsquo;98</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:31.1%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:60.9%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;50</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;98 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">4th Ed &rsquo;04</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:24.8%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:45.3%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;40</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;73 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">5th Ed &rsquo;08</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:37.3%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:61.5%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;60</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;99 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">6th Ed &rsquo;12</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:40.4%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:59.0%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;65</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;95 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">7th Ed &rsquo;14</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:46.6%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:65.2%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;75</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;105 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">8th Ed &rsquo;17</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:59.0%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:79.5%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;95</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;128 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">9th Ed &rsquo;20</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:77.6%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:100%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;125</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;161 adj</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#c8bfb0;text-align:right;">10th Ed &rsquo;23</div>
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="height:9px;background:#c8922a;border-radius:3px;width:93.2%;"></div>
        <div style="height:9px;background:rgba(240,192,96,0.28);border-radius:3px;width:98.8%;"></div>
      </div>
      <div style="font-size:0.74rem;line-height:1.4;">
        <div style="color:#c8922a;font-weight:700;">&pound;150</div>
        <div style="color:rgba(240,192,96,0.5);font-size:0.68rem;">&pound;159 adj</div>
      </div>
    </div>

    <div style="height:1px;background:#2a2e3a;margin:0.75rem 0;"></div>
    <div style="display:grid;grid-template-columns:110px 1fr 110px;align-items:center;gap:0.5rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.72rem;text-transform:uppercase;color:#5c6480;text-align:right;">Total change</div>
      <div></div>
      <div style="font-size:0.72rem;line-height:1.4;color:#5c6480;">+109% adj &nbsp;|&nbsp; 106% inflation</div>
    </div>

  </div>
</div>

<!-- ── UK DATA TABLE ──────────────────────────────────────────────────── -->
<table>
  <thead>
    <tr>
      <th>Edition</th>
      <th>Box Name</th>
      <th>Year</th>
      <th>Launch Price (GBP)</th>
      <th>What That Price Is Worth in 2026 (GBP)</th>
      <th>Price Change vs. Prior Edition (Inflation-Adjusted)</th>
      <th>Cumulative Inflation During Edition Lifespan</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>2nd Ed</strong></td>
      <td>2nd Edition Starter Box</td>
      <td>1993</td>
      <td>&pound;34.99</td>
      <td>&pound;76</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
    </tr>
    <tr>
      <td><strong>3rd Ed</strong></td>
      <td>3rd Edition Starter</td>
      <td>1998</td>
      <td>&pound;50</td>
      <td>&pound;98</td>
      <td style="color:#d44040;font-weight:600;">+29%</td>
      <td>11%</td>
    </tr>
    <tr>
      <td><strong>4th Ed</strong></td>
      <td>Battle for Macragge</td>
      <td>2004</td>
      <td>&pound;40</td>
      <td>&pound;73</td>
      <td style="color:#4aab72;font-weight:600;">&#8722;26%</td>
      <td>8%</td>
    </tr>
    <tr>
      <td><strong>5th Ed</strong></td>
      <td>Assault on Black Reach</td>
      <td>2008</td>
      <td>&pound;60</td>
      <td>&pound;99</td>
      <td style="color:#d44040;font-weight:600;">+36%</td>
      <td>11%</td>
    </tr>
    <tr>
      <td><strong>6th Ed</strong></td>
      <td>Dark Vengeance</td>
      <td>2012</td>
      <td>&pound;65</td>
      <td>&pound;95</td>
      <td style="color:#4aab72;font-weight:600;">&#8722;4%</td>
      <td>13%</td>
    </tr>
    <tr>
      <td><strong>7th Ed</strong></td>
      <td>Dark Vengeance</td>
      <td>2014</td>
      <td>&pound;75</td>
      <td>&pound;105</td>
      <td style="color:#f0c060;font-weight:600;">+11%</td>
      <td>4%</td>
    </tr>
    <tr>
      <td><strong>8th Ed</strong></td>
      <td>Dark Imperium</td>
      <td>2017</td>
      <td>&pound;95</td>
      <td>&pound;128</td>
      <td style="color:#d44040;font-weight:600;">+22%</td>
      <td>3%</td>
    </tr>
    <tr>
      <td><strong>9th Ed</strong></td>
      <td>Indomitus</td>
      <td>2020</td>
      <td>&pound;125</td>
      <td>&pound;161</td>
      <td style="color:#d44040;font-weight:600;">+26%</td>
      <td>5%</td>
    </tr>
    <tr>
      <td><strong>10th Ed</strong></td>
      <td>Leviathan</td>
      <td>2023</td>
      <td>&pound;150</td>
      <td>&pound;159</td>
      <td style="color:#4aab72;font-weight:600;">&#8722;1%</td>
      <td>22%</td>
    </tr>
    <tr style="border-top:1px solid #3a3e4a;">
      <td colspan="3" style="font-family:Oswald,sans-serif;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.04em;color:#7a8090;">Across All Editions</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#d44040;font-weight:600;">+109%</td>
      <td>106%</td>
    </tr>
  </tbody>
</table>

<h2>What Did Players Get in the Box?</h2>

<p style="font-size:0.82rem;color:var(--text-muted);margin-top:-0.5rem;"><strong>Standard Game Size</strong> is an estimated metric based on online research. It attempts to create an apples-to-apples comparison between editions where games were played at different point values. For example, earlier editions were often played at lower point totals than the standard 2,000 points, so points-per-dollar figures are scaled up to account for those smaller game sizes.</p>

<!-- ── POINTS PER DOLLAR BAR CHART ────────────────────────────────────── -->
<div style="background:#1c2230;border-radius:10px;padding:1.25rem 1.5rem;margin:1.75rem 0;overflow-x:auto;">
  <div style="font-family:Oswald,sans-serif;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;color:#c8bfb0;margin-bottom:0.25rem;">Points per 2026 Dollar (Adjusted for Game Size)</div>
  <div style="font-size:0.72rem;color:#5c6480;margin-bottom:1.1rem;">Higher is better value. Green = great (&ge;9 pts/$) &nbsp;&middot;&nbsp; Gold = decent (7&ndash;9 pts/$) &nbsp;&middot;&nbsp; Red = poor (&lt;7 pts/$).</div>
  <div style="min-width:300px;">

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">3rd Ed &rsquo;98</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:34.9%;background:#d44040;border-radius:4px;opacity:0.75;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#d44040;text-align:right;">3.7 pts/$</div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">4th Ed &rsquo;04</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:63.2%;background:#d44040;border-radius:4px;opacity:0.75;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#d44040;text-align:right;">6.7 pts/$</div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">5th Ed &rsquo;08</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:94.3%;background:#4aab72;border-radius:4px;opacity:0.85;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#4aab72;text-align:right;">10.0 pts/$</div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#c8bfb0;text-align:right;">6th Ed &rsquo;12 &#9733;</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:100%;background:#4aab72;border-radius:4px;opacity:0.85;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#4aab72;text-align:right;">10.6 pts/$</div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">7th Ed &rsquo;14</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:93.4%;background:#4aab72;border-radius:4px;opacity:0.85;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#4aab72;text-align:right;">9.9 pts/$</div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">8th Ed &rsquo;17</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:68.9%;background:#c8922a;border-radius:4px;opacity:0.85;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#c8922a;text-align:right;">7.3 pts/$</div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#7a8090;text-align:right;">9th Ed &rsquo;20</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:74.5%;background:#c8922a;border-radius:4px;opacity:0.85;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#c8922a;text-align:right;">7.9 pts/$</div>
    </div>

    <div style="display:grid;grid-template-columns:110px 1fr 70px;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
      <div style="font-family:Oswald,sans-serif;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.03em;color:#c8bfb0;text-align:right;">10th Ed &rsquo;23</div>
      <div style="height:22px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;position:relative;">
        <div style="position:absolute;left:0;top:0;height:100%;width:63.2%;background:#d44040;border-radius:4px;opacity:0.75;"></div>
      </div>
      <div style="font-size:0.8rem;font-weight:700;color:#d44040;text-align:right;">6.7 pts/$</div>
    </div>

  </div>
</div>

<!-- ── POINTS DATA TABLE ──────────────────────────────────────────────── -->
<table>
  <thead>
    <tr>
      <th>Edition</th>
      <th>Year</th>
      <th>Launch Price (USD)</th>
      <th>What That Price Is Worth in 2026 (USD)</th>
      <th>Points in Box at Launch</th>
      <th>Points Scaled to a Standard 2,000pt Game</th>
      <th>Points per 2026 Dollar (Raw)</th>
      <th>Points per 2026 Dollar (Scaled to 2,000pt Game)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>2nd Ed</strong></td>
      <td>1993</td>
      <td>$60</td>
      <td>$136</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
      <td style="color:#5c6480;">&#8212;</td>
    </tr>
    <tr>
      <td><strong>3rd Ed</strong></td>
      <td>1998</td>
      <td>$90</td>
      <td>$180</td>
      <td>500</td>
      <td>667</td>
      <td>2.8</td>
      <td style="color:#d44040;font-weight:600;">3.7</td>
    </tr>
    <tr>
      <td><strong>4th Ed</strong></td>
      <td>2004</td>
      <td>$75</td>
      <td>$130</td>
      <td>650</td>
      <td>867</td>
      <td>5.0</td>
      <td style="color:#d44040;font-weight:600;">6.7</td>
    </tr>
    <tr>
      <td><strong>5th Ed</strong></td>
      <td>2008</td>
      <td>$75</td>
      <td>$114</td>
      <td>1,000</td>
      <td>1,143</td>
      <td>8.8</td>
      <td style="color:#4aab72;font-weight:600;">10.0</td>
    </tr>
    <tr>
      <td><strong>6th Ed &#9733;</strong></td>
      <td>2012</td>
      <td>$100</td>
      <td>$142</td>
      <td>1,500</td>
      <td>1,500</td>
      <td>10.6</td>
      <td style="color:#4aab72;font-weight:600;">10.6</td>
    </tr>
    <tr>
      <td><strong>7th Ed</strong></td>
      <td>2014</td>
      <td>$110</td>
      <td>$152</td>
      <td>1,500</td>
      <td>1,500</td>
      <td>9.9</td>
      <td style="color:#4aab72;font-weight:600;">9.9</td>
    </tr>
    <tr>
      <td><strong>8th Ed</strong></td>
      <td>2017</td>
      <td>$160</td>
      <td>$213</td>
      <td>1,550</td>
      <td>1,550</td>
      <td>7.3</td>
      <td style="color:#c8922a;font-weight:600;">7.3</td>
    </tr>
    <tr>
      <td><strong>9th Ed</strong></td>
      <td>2020</td>
      <td>$200</td>
      <td>$253</td>
      <td>2,000</td>
      <td>2,000</td>
      <td>7.9</td>
      <td style="color:#c8922a;font-weight:600;">7.9</td>
    </tr>
    <tr>
      <td><strong>10th Ed</strong></td>
      <td>2023</td>
      <td>$250</td>
      <td>$268</td>
      <td>1,800</td>
      <td>1,800</td>
      <td>6.7</td>
      <td style="color:#d44040;font-weight:600;">6.7</td>
    </tr>
  </tbody>
</table>
<p style="font-size:0.78rem;color:var(--text-muted);">&#9733; Best all-time value per inflation-adjusted dollar.</p>

<h2>Top Takeaways</h2>

<h3>1. Price Increases Have Been Tame Relative to Long-Term Inflation (But There Is a Catch)</h3>

<p>Looking at the raw numbers, Warhammer 40K launch boxes have clearly increased in price over time. However, Warhammer price increases in total have been tame relative to the increases in other goods and services over the last 30 years.</p>

<p>One major reason is Games Workshop's shift away from metal models in the late 1990s and early 2000s. The transition to plastic reduced manufacturing costs and allowed them to price products more competitively. If we were to ignore that period in the calculation (2012&ndash;2023), Warhammer US inflation-adjusted prices increased 89% versus cumulative inflation of 33%.</p>

<p>The last 10 years have not been kind to consumers. A lack of innovation, combined with Warhammer's peak popularity, appears to have given Games Workshop the ability to raise prices far more aggressively than in previous decades.</p>

<h3>2. The UK Has Been Most Impacted by Rising Prices</h3>

<p>Known as the cheapest place to buy Warhammer, the UK has seen prices rise faster than the US throughout history. Despite lower average annual inflation than the US, Games Workshop appears to be pushing prices higher in its home market.</p>

<p>In my opinion, this is likely due to the lower overall price baseline. It's far easier to convince a player in the UK to pay &pound;25 more when their launch box was previously &pound;100, compared to the US where players were already paying closer to $200.</p>

<h3>3. The Best Time to Buy Warhammer Was During the Worst Times</h3>

<p>I may be going out on a limb here as someone who didn't play older editions, but based on research and community sentiment, 6th and 7th editions were widely considered among the weakest editions of 40K. Now I don't know that for sure, but it seems like 40K was not in the best state during that time.</p>

<p>Yet, launch boxes during this period delivered some of the best value in terms of points per dollar. It appears that when Games Workshop's back is against the wall, they are more likely to offer stronger value to players.</p>

<h3>4. Model Count Has Been GW's Primary Mechanism to Provide Value</h3>

<p>We have too many models on the table today. The chart data proves this unequivocally. Model counts in launch boxes have increased roughly 33% since 6th edition, yet total points in the box have only increased by about 17%.</p>

<p>Warhammer 40K price hikes are increasingly driven by the volume of miniatures required to play a standard game. It's not about buying one or two kits to plug holes in our list, rather it's being forced to routinely spend hundreds of dollars to run specialized detachments or access a particular playstyle. If fewer models were required to play, individual price hikes for combo boxes and kits might feel easier to swallow.</p>

<h3>5. Launch Boxes Are Still Amazing Value</h3>

<p>Regardless of rising prices, launch boxes remain one of the best values in all of Warhammer 40K.</p>

<p>If you split a launch box with a friend, your entry cost for roughly 1,000 points could be under $150. That's excellent value, especially when many Combat Patrols struggle to reach 500 points. Before you buy, check our <a href="/products/">price comparison tool</a> to see which retailer has the best deal on the current starter box. Prices vary more than you'd expect.</p>

<h2>Predicting 11th Edition's Price</h2>

<p>I have no idea what 11th edition's price will be. However, based on the data, I do have a strong hunch it will fall between $285&ndash;$300 USD.</p>

<table>
  <thead>
    <tr>
      <th>Scenario</th>
      <th>Price</th>
      <th>Reasoning</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Low End</strong></td>
      <td style="color:#4aab72;font-weight:700;">$285</td>
      <td>GW provides close to 2,000 total points, similar to recent editions, at roughly 7 points per dollar &mdash; in line with recent trends.</td>
    </tr>
    <tr>
      <td><strong>High End</strong></td>
      <td style="color:#d44040;font-weight:700;">$300</td>
      <td>Follows the pattern of $40 increases (7th&rarr;8th, 8th&rarr;9th) and the $50 jump from 9th&rarr;10th, suggesting a further $50 increase is plausible.</td>
    </tr>
  </tbody>
</table>

<p>Additionally, inflation was unusually high between 2020 and 2023. Games Workshop may view 11th Edition and the rising popularity of Warhammer as an opportunity to adjust pricing higher than expected in order to satisfy internal profitability goals that may have been impacted by the pandemic and inflation.</p>

<h2>Conclusion</h2>

<p>Launch boxes are clearly becoming more premium over time, focused less on being a simple entry point for newcomers and more on helping existing players start new armies or expand existing collections.</p>

<p>Can we conclude that Games Workshop is simply a greedy corporation pushing prices at all costs? At this point in our Economics of Warhammer journey, the answer is no.</p>

<p>Games Workshop in the past has done an admirable job in improving the value of launch boxes even during periods of price hikes. Even during 2020&ndash;2023, a period marked by high inflation, a global pandemic, and logistics disruptions, launch box prices remained relatively reasonable. While recent history has painted a less favorable picture for Games Workshop's launch box prices, points per dollar remains above average and model count is high.</p>

<p>In general I don't excuse Games Workshop's overall pricing practices, but for Part 1, I would cautiously score this as a point in Games Workshop's favor. Launch boxes despite their price increases over the last few editions are still relatively affordable (especially when split with a friend) and provide a ton of plastic all in one curated box with models that will remain relevant for years to come.</p>

<p>If you disagree, let me know what you think and if I made any errors in my data, I'd love to hear that as well.</p>
"""


class Command(BaseCommand):
    """Publish the Economics of Warhammer Part 1 blog post (idempotent)."""

    help = 'Publishes the Warhammer 40K launch box economics Part 1 post.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite the post body/meta even if it already exists.',
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
            title='Is Warhammer 40K Getting More Expensive? Launch Box Prices from 2nd to 10th Edition',
            excerpt=(
                'We went back in time and compared every Warhammer 40K launch box from 2nd '
                'Edition through 10th Edition -- adjusting for inflation. The results might '
                'surprise you. Part 1 of the Economics of Warhammer series.'
            ),
            body=BODY,
            status=Post.STATUS_PUBLISHED,
            published_at=timezone.now(),
            meta_title='Is Warhammer 40K Getting More Expensive? Launch Box Prices 2nd-10th Ed',
            meta_description=(
                'Inflation-adjusted 40K launch box prices from 2nd to 10th Edition. '
                'Is GW pricing fair? The data might surprise you. Part 1 of Economics of Warhammer.'
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

        tag_names = ['Economics', 'Pricing', 'Warhammer 40K', 'Data', 'Budget Tips']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)
        self.stdout.write(self.style.SUCCESS(f'Tags attached: {tag_names}'))
