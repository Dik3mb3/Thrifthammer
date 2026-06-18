"""
Publish: Warhammer 40K 11th Edition Core Keywords Cheat Sheet

Idempotent -- safe to run repeatedly. Use --force to overwrite an existing post.
"""
import datetime

from django.core.management.base import BaseCommand

SLUG = 'warhammer-40k-11th-edition-core-keywords-cheat-sheet'

BODY = """
<p>Today we are going over the core keywords of 11th Edition, focusing on what's changed compared to 10th Edition.</p>

<p>This won't be a wordy article that talks about each keyword in depth. This is aimed at getting all players primed and ready to play 11th Edition by reducing any confusion caused by slight changes to the wording of rules. The 11th Edition weapon and core keyword cheat sheet we provided below is downloadable, printable, and editable. If we made a mistake or our wording is unclear, make the edit yourself!</p>

<p>We aggregated all of these keywords through 3rd party articles and videos. We did not have access to early review copies of the rulebook. If there are any issues, please contact us and we will be happy to make edits.</p>

<div id="kw-dl-btns">
  <a href="#" class="btn btn-primary kw-print-btn">Download PDF</a>
  <a href="#" class="btn btn-secondary kw-docx-btn">Download Editable Version</a>
</div>

<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500&display=swap');

/* ── Shared ── */
#kw-dl-btns { display: flex; gap: .75rem; flex-wrap: wrap; margin: 1.25rem 0 2rem }

/* Print masthead hidden on screen */
.kw-print-masthead { display: none }

/* ── Screen: section headers — red bar pops on dark page ── */
h3.kw-section {
  font-size: .82rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: #fff;
  background: #b52020;
  padding: .5rem .9rem;
  margin: 2.25rem 0 .5rem;
  border-radius: 4px;
}

/* ── Screen: keyword entry — white card on dark background ── */
.kw-entry {
  background: #ffffff;
  border-radius: 6px;
  border-left: 4px solid #b52020;
  padding: .9rem 1rem;
  margin-bottom: .45rem;
}

/* Name + badge on same flex row */
.kw-head {
  display: flex;
  align-items: baseline;
  gap: .65rem;
  flex-wrap: wrap;
  margin-bottom: .2rem;
}
h4.kw-name {
  font-size: 1.2rem;
  font-weight: 800;
  color: #111111;
  margin: 0;
}

/* Example weapon or unit */
p.kw-sub {
  margin: .1rem 0 .35rem;
  font-size: .83rem;
  color: #666666;
  font-style: italic;
}

/* Same / Changed badge */
.kw-badge {
  display: inline-block;
  font-size: .68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  padding: 2px 9px;
  border-radius: 3px;
  white-space: nowrap;
  flex-shrink: 0;
}
.kw-badge-same { background: #e8f5e4; color: #1e6b00 }
.kw-badge-diff { background: #fce8e8; color: #8c1515 }

/* Effect text — explicit dark so it reads on white card */
p.kw-effect { margin: 0; line-height: 1.6; color: #2e2e2e; font-size: .95rem }

/* What changed callout */
.kw-changed {
  margin: .6rem 0 0;
  padding: .45rem .75rem;
  background: #fde8e8;
  border-left: 3px solid #b52020;
  border-radius: 3px;
  font-size: .88em;
  color: #333333;
  line-height: 1.5;
}
.kw-changed strong { color: #b52020 }

/* ── Print: 2-column portrait cheat sheet ── */
@media print {
  @page { size: A4 portrait; margin: 8mm }

  /* Hide blog chrome */
  .navbar, .footer, .blog-breadcrumbs, .blog-article-header,
  .blog-article-img-wrap, .blog-inline-newsletter, .blog-related,
  .blog-post-cta, .comments-section, .blog-article-footer,
  .blog-sidebar, #kw-dl-btns { display: none !important }
  .blog-article-body > p { display: none !important }

  /* Flatten ancestor containers */
  html, body { width: 100% !important; margin: 0 !important; padding: 0 !important; background: none !important }
  .page-content { padding: 0 !important; margin: 0 !important; background: none !important }
  .blog-detail-layout { display: block !important; padding: 0 !important; margin: 0 !important; max-width: none !important; gap: 0 !important }
  .blog-article { padding: 0 !important; margin: 0 !important; width: 100% !important; max-width: none !important; min-width: 0 !important }
  .blog-article-body { padding: 0 !important; margin: 0 !important; width: 100% !important; overflow: visible !important }
  /* .prose table { display: block } clips content — override */
  .prose table { display: table !important; overflow: visible !important; max-width: none !important }

  /* Show screen cards as 2-column cheat sheet */
  .kw-screen-only {
    display: block !important;
    column-count: 2;
    column-gap: 7mm;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  /* Masthead spans both columns at the top */
  .kw-print-masthead {
    display: flex !important;
    column-span: all;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 10px;
    background: #1e1e1e !important;
    padding: 8px 11px 7px;
    margin-bottom: 10px;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .kw-print-masthead .cs-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 18px;
    font-weight: 800;
    color: #ffffff !important;
    text-transform: uppercase;
    letter-spacing: .06em;
    line-height: 1;
  }
  .kw-print-masthead .cs-edition {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 9.5px;
    font-weight: 600;
    color: #b52020 !important;
    text-transform: uppercase;
    letter-spacing: .1em;
  }
  .kw-print-masthead .cs-legend { margin-left: auto; display: flex; gap: 12px; align-items: center }
  .kw-print-masthead .cs-leg-item {
    display: flex; align-items: center; gap: 4px;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: .05em; color: #cccccc !important;
  }
  .kw-print-masthead .cs-dot {
    width: 11px; height: 11px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 7px; font-weight: 800; color: #ffffff !important;
  }
  .kw-print-masthead .cs-dot-same { background: #2a6b1a !important }
  .kw-print-masthead .cs-dot-diff { background: #b52020 !important }

  /* Compact card styles for print */
  .kw-screen-only .kw-entry {
    padding: .45rem .6rem !important;
    margin-bottom: 3px !important;
    break-inside: avoid !important;
    border-radius: 3px !important;
    border-left-width: 3px !important;
    background: #ffffff !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .kw-screen-only h3.kw-section {
    break-inside: avoid !important;
    margin: 6px 0 3px !important;
    padding: .28rem .65rem !important;
    font-size: .72rem !important;
    background: #b52020 !important;
    border-radius: 3px !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .kw-screen-only .kw-head { margin-bottom: .1rem !important }
  .kw-screen-only h4.kw-name { font-size: .87rem !important; margin: 0 !important }
  .kw-screen-only p.kw-sub { font-size: .72rem !important; margin: .04rem 0 .15rem !important }
  .kw-screen-only p.kw-effect { font-size: .78rem !important; line-height: 1.38 !important; color: #2e2e2e !important }
  .kw-screen-only .kw-changed {
    margin-top: .28rem !important;
    padding: .22rem .48rem !important;
    font-size: .72rem !important;
    color: #333333 !important;
    background: #fde8e8 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .kw-screen-only .kw-badge { font-size: .59rem !important; padding: 1px 5px !important }
}
</style>

<!-- ═══════════════════════════════════ SCREEN + PRINT CONTENT ════════════════════════════════ -->
<div class="kw-screen-only">

<!-- Print masthead: hidden on screen, spans both columns at top of PDF -->
<div class="kw-print-masthead">
  <span class="cs-title">Core Keywords</span>
  <span class="cs-edition">Warhammer 40,000 | 11th Edition Quick Reference</span>
  <div class="cs-legend">
    <div class="cs-leg-item"><span class="cs-dot cs-dot-same">&#10003;</span> Same as 10th</div>
    <div class="cs-leg-item"><span class="cs-dot cs-dot-diff">&#10007;</span> Changed in 11th</div>
  </div>
</div>

<h3 class="kw-section">Shooting Keywords</h3>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Assault</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Bolt Rifle</p>
  <p class="kw-effect">Advance and shoot with no penalty to hit. Roll D6, add to movement, then fire at your regular BS. No Actions or Charges after Advancing.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Heavy</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Melter Rifle (Eradicator)</p>
  <p class="kw-effect">+1 to Hit if every model in the unit moved less than 3&rdquo; last turn. All-or-nothing for the unit. Does not apply in Engagement Range or when setting up from deep strike or transport.</p>
  <p class="kw-changed"><strong>What changed:</strong> Previously required the whole unit to remain stationary. Now allows up to 3&rdquo; of movement.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Rapid Fire X</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Rapid Fire Battle Cannon</p>
  <p class="kw-effect">Gain X extra shots when the target is within half the weapon&rsquo;s range. Judged model by model. X can be a flat number or a dice expression.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Ignores Cover</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Purifying Flame</p>
  <p class="kw-effect">Ignore the -1 BS penalty targets gain from Cover. Fire at full unmodified BS regardless of terrain or Stealth.</p>
  <p class="kw-changed"><strong>What changed:</strong> Cover now imposes -1 BS in 11th. Also redundant on Torrent weapons, which bypass hit rolls entirely.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Torrent</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Baleflamer (Heldrake)</p>
  <p class="kw-effect">Attacks automatically hit, no Hit roll made. BS shown as N/A. Number of hits comes directly from the weapon&rsquo;s Attacks stat. Inherently bypasses Cover. In Overwatch, the automatic hit applies where other weapons would only hit on 6+.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Indirect Fire</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Mortars, Artillery</p>
  <p class="kw-effect">May target units not visible to the firer. Penalties: target always has Cover (-1 BS); no re-rolls to Hit; cannot fire while in Engagement Range. No spotter: hits only on 6+. Stationary with spotter: 4+ at best. Can fire normally if line of sight is available.</p>
  <p class="kw-changed"><strong>What changed:</strong> New layered penalty system and explicit ban on use from Engagement Range.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Blast (X)</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Leman Russ Battle Cannon</p>
  <p class="kw-effect">+1 Attack per 5 full models in the target unit, rounded down. Blast X multiplies that bonus per 5 models. Cannot target units in Engagement Range under any circumstances.</p>
  <p class="kw-changed"><strong>What changed:</strong> Blast X multiplier is new in 11th. In 10th only a flat +1 per 5 models with no multiplier.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">One-Shot</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Hunter-Killer Missile</p>
  <p class="kw-effect">Fire once per game. The bearer may not use this weapon again for the rest of the battle.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Close Quarters</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Bolt Pistol (formerly Pistol)</p>
  <p class="kw-effect">Shoot while in Engagement Range. Includes the Pistol keyword and will eventually replace it.</p>
  <p class="kw-changed"><strong>What changed:</strong> Renamed from Pistol.</p>
</div>

<h3 class="kw-section">Hit Roll Keywords</h3>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Psychic</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Warp Blast (Zoanthrope)</p>
  <p class="kw-effect">Attacks ignore all modifiers to the Hit roll in both shooting and melee. Penalties from Cover, Stealth, or any enemy special rule are disregarded. Enemy anti-psyker units may still use Feel No Pain saves against these attacks.</p>
  <p class="kw-changed"><strong>What changed:</strong> Previously just a tag for enemy resistance. Now grants ignore-all-hit-modifiers.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Lethal Hits</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Bile Blade (Great Unclean One)</p>
  <p class="kw-effect">Unmodified Hit rolls of 6 automatically wound with no Wound roll needed. Set these aside after hitting; roll remaining hits to wound normally. Auto-wounds from Lethal Hits are not Critical Wounds, so the target may still save against them.</p>
  <p class="kw-changed"><strong>What changed:</strong> Auto-wound on a 6 is now optional. Skip it if the weapon also has Anti and Devastating Wounds.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Sustained Hits X</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Lelith Hesperax</p>
  <p class="kw-effect">Unmodified Hit rolls of 6 generate X additional automatic hits alongside the original. Bonus hits are not Critical Hits. If combined with Lethal Hits: one auto-wound from the original critical hit, plus X bonus hits that must still be rolled to wound normally.</p>
</div>

<h3 class="kw-section">Wound Roll Keywords</h3>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Devastating Wounds</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Assault Cannon (Terminator)</p>
  <p class="kw-effect">Critical Wounds (unmodified 6s to wound, or lower with Anti) bypass all Armor and Invulnerable saves. Only Feel No Pain applies. Each Critical Wound affects at most one model regardless of Damage value.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Anti (X)</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Haywire Blaster, Anti-Vehicle 4+</p>
  <p class="kw-effect">Written as Anti-[keyword] X+. Wound rolls that meet or beat X+ against a unit with the matching keyword count as Critical Wounds and always succeed. Pairs with Devastating Wounds to convert those crits to Mortal Wounds.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Melta X</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Melter Rifle (Melta 2)</p>
  <p class="kw-effect">+X Damage when firing within half range. Judged model by model, roll separately for models inside and outside half range. Damage-reducing effects are applied after the Melta bonus is added.</p>
  <p class="kw-changed"><strong>What changed:</strong> Sequence clarified: base damage first, then add Melta bonus, then apply damage-reduction effects.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Twin-Linked</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Aggressor (ranged and melee)</p>
  <p class="kw-effect">Re-roll Wound rolls. Works on both ranged and melee profiles.</p>
</div>

<h3 class="kw-section">Melee Keywords</h3>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Cleave X</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Custom Choppa (Warboss)</p>
  <p class="kw-effect">+1 melee Attack per 5 full models in the target unit, multiplied by X. All attacks with that profile must target the same unit to gain the bonus. Splitting attacks across units forfeits Cleave.</p>
  <p class="kw-changed"><strong>What changed:</strong> Brand new in 11th. The melee equivalent of Blast. No equivalent existed in 10th Edition.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Lance</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Hunting Lance (Rough Rider)</p>
  <p class="kw-effect">+1 to Wound rolls if the bearer&rsquo;s unit Charged this turn.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Extra Attacks</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Bile Blade secondary profile</p>
  <p class="kw-effect">Normally a model fights with one melee weapon per activation. Extra Attack profiles may be used simultaneously alongside the primary weapon.</p>
  <p class="kw-changed"><strong>What changed:</strong> +Attacks modifiers now also apply to Extra Attack profiles. Previously they did not.</p>
</div>

<h3 class="kw-section">Special Keywords</h3>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Precision</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Exodus Pistol (Vindicare)</p>
  <p class="kw-effect">When attacking a unit containing a visible Character, allocate wounds to that Character first before other models. Excess damage spills to the rest of the unit. Works in shooting and melee.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Hazardous</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Plasma Incinerator (Hellblasters)</p>
  <p class="kw-effect">After attacking, roll 1D6 per Hazardous weapon used by the unit. On a 1 or 2: unit suffers 1 Mortal Wound (3 if a Monster or Vehicle). No saves of any kind, only Feel No Pain. If a Character fires the weapon, the mortal wound goes to them, not the bodyguard unit.</p>
  <p class="kw-changed"><strong>What changed:</strong> Previously failed on 1, removed a model. Now fails on 1-2, deals 1 MW. Characters still take it personally.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Conversion</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-sub">Conversion Beamer (Leagues of Votann)</p>
  <p class="kw-effect">Does more damage at longer range rather than shorter. Exact bonuses vary by datasheet. One variant grants Critical Hits on a 4+ beyond 12&rdquo;. Specific trigger and effect always defined on the individual weapon datasheet.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Hunter (X)</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-sub">Rules in Core Rule Companion</p>
  <p class="kw-effect">Can only target units with the specified keyword. Represents specialised weapons that are useless against other target types such as EMP grenades or creature-specific weapons.</p>
  <p class="kw-changed"><strong>What changed:</strong> New in 11th. Rules in Core Rule Companion, not the main rulebook.</p>
</div>

<h3 class="kw-section">Core Unit Keywords</h3>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Deep Strike</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Unit starts the game in Reserves. Deploys at the end of any Movement Phase, placed anywhere more than 8&rdquo; from enemy units.</p>
  <p class="kw-changed"><strong>What changed:</strong> Minimum distance reduced from 9&rdquo; to 8&rdquo; to match new charge rules.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Deadly Demise X</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">When the unit is destroyed, roll a D6. On a 6, deal X Mortal Wounds to all units within range. For Transports, triggers after any units disembark.</p>
  <p class="kw-changed"><strong>What changed:</strong> For Transports, now triggers after units disembark rather than before.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Feel No Pain X+</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-effect">Each time this unit suffers a wound, roll a D6. On a result of X+, that wound is ignored.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Fights First</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Lets a unit fight before units without this ability. The player whose turn it is picks a unit first, including when both sides have Fights First. A unit that Charged will get to strike before enemy Fights First units.</p>
  <p class="kw-changed"><strong>What changed:</strong> Active player now picks first. Makes this slightly less dominant than in 10th.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Firing Deck X</h4>
    <span class="kw-badge kw-badge-same">&#10003; Same as 10th</span>
  </div>
  <p class="kw-effect">A Transport ability. Up to X models embarked inside may shoot using their own weapons as if they were the Transport, using the Transport&rsquo;s firing position.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Heal X</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">When a unit is Healed, check for models with missing wounds and restore one wound per Heal. If no wounded models exist, return one model at 1 wound. Repeat X times. If targeting a single model, excess heals are wasted.</p>
  <p class="kw-changed"><strong>What changed:</strong> Brand new keyword. Standardizes wound recovery and model return into one unified mechanic.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Hover</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Unit ignores the -2&rdquo; movement penalty normally applied when using the Fly keyword to move over terrain.</p>
  <p class="kw-changed"><strong>What changed:</strong> Brand new keyword splitting Fly movement into standard (-2&rdquo;) and Hover (no penalty).</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Infiltrators</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Unit can be set up anywhere on the battlefield more than 8&rdquo; from enemy deployment zones and more than 8&rdquo; from all enemy units.</p>
  <p class="kw-changed"><strong>What changed:</strong> Minimum distance reduced from 9&rdquo; to 8&rdquo; to match new charge rules.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Lone Operative</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Cannot be targeted by ranged attacks unless the attacking model is within a certain distance. Default is 12&rdquo; but may be listed as Lone Operative X&rdquo; on specific datasheets.</p>
  <p class="kw-changed"><strong>What changed:</strong> Now has X qualifier. Specific datasheets can set a different distance instead of always 12&rdquo;.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Plunging Fire</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">When shooting from a position at least 3&rdquo; higher than the target, the attacking unit gains +1 BS. This effectively counters the Cover penalty.</p>
  <p class="kw-changed"><strong>What changed:</strong> Now applies to most terrain in the game.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Scouts X&rdquo;</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Before the first turn, the unit may make a free move of up to X&rdquo;. Cannot be used if deployed outside your deployment zone. If starting in Strategic Reserves, may instead set up anywhere in your deployment zone at the start of Battle Round 1.</p>
  <p class="kw-changed"><strong>What changed:</strong> No longer works if deployed outside your deployment zone. New option to set up from Strategic Reserves instead.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Stealth</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Provides the Benefit of Cover out in the open.</p>
  <p class="kw-changed"><strong>What changed:</strong> In 10th imposed -1 to Hit directly. Now grants Cover (-1 BS) instead.</p>
</div>

<div class="kw-entry">
  <div class="kw-head">
    <h4 class="kw-name">Surge Moves</h4>
    <span class="kw-badge kw-badge-diff">&#10007; Changed in 11th</span>
  </div>
  <p class="kw-effect">Allows a unit to move after being shot at, including moving into Engagement Range. Cannot be used if the unit already moved this phase. The unit must move as close to the target as possible.</p>
  <p class="kw-changed"><strong>What changed:</strong> Now its own rules section. Cannot use if already moved this phase. Must move toward the target.</p>
</div>

</div><!-- end .kw-screen-only -->

<p>Going into 11th Edition, we plan on releasing more content like this to help with the transition to a new edition. To keep up with new articles and the best Warhammer deals online, sign up for our newsletter below. If you have any ideas for new content we should cover, please contact us directly.</p>
"""


class Command(BaseCommand):
    """Publish the 11th Edition core keywords cheat sheet blog post."""

    help = 'Publish the Warhammer 40K 11th Edition core keywords cheat sheet (idempotent)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Overwrite the post if it already exists.',
        )

    def handle(self, *args, **options):
        from blog.models import Post, Tag

        existing = Post.objects.filter(slug=SLUG).first()
        if existing and not options['force']:
            self.stdout.write(
                f'Post "{SLUG}" already exists -- skipping. Use --force to overwrite.'
            )
            return

        defaults = {
            'title': 'Warhammer 40K 11th Edition Core Keywords Cheat Sheet',
            'excerpt': (
                'The complete 11th Edition weapon and core keywords cheat sheet. '
                'Every keyword explained with side-by-side 10th vs 11th edition changes. '
                'Downloadable as PDF or editable Word document.'
            ),
            'body': BODY,
            'status': Post.STATUS_PUBLISHED,
            'published_at': datetime.datetime(2026, 6, 17, 10, 0, 0,
                                              tzinfo=datetime.timezone.utc),
            'meta_title': 'Warhammer 40K 11th Edition Core Keywords Cheat Sheet | ThriftHammer',
            'meta_description': (
                'The complete Warhammer 40K 11th edition core and weapon keywords cheat sheet. '
                'Covers what changed from 10th edition. Download as PDF or editable Word doc.'
            ),
            'featured_image_url': '/static/images/blog/11th-edition-keywords-featured.png',
            'featured_image_alt': 'Warhammer 40K 11th Edition Weapon and Core Keywords Cheat Sheet - ThriftHammer',
        }

        if existing and options['force']:
            for key, value in defaults.items():
                setattr(existing, key, value)
            existing.save()
            post = existing
            self.stdout.write('Updated existing post.')
        else:
            post = Post(slug=SLUG, **defaults)
            post.save()
            self.stdout.write('Created new post.')

        tag_names = ['Warhammer 40K', 'Rules & FAQs']
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            post.tags.add(tag)

        self.stdout.write(self.style.SUCCESS(
            f'Published: "{post.title}" -> /blog/{SLUG}/'
        ))
