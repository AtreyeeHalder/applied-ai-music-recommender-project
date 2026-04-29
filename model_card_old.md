# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**CadenceMatcher 1.0**  

---

## 2. Intended Use  

CadenceMatcher recommends songs from a small catalog based on a listener's stated genre, mood, energy, and acoustic preferences. It returns a ranked list of the top five songs that best match those preferences.

It assumes the user already knows what they like and can describe it in simple terms. It does not learn from listening history or adapt over time.

This system is built for classroom exploration to analyze how scoring rules and different data choices affect recommendations.

---

## 3. How the Model Works  

Each song in the catalog has a genre, mood, energy level (0 to 1), and an acousticness value (0 to 1). The system compares those values against the user's stated preferences and adds up points.

- If the song's genre matches what the user likes, it gets 1 point.
- If the song's mood matches, it gets 1.5 points.
- The closer the song's energy is to the user's target energy, the more points it earns — up to 3 points for a perfect match.
- If the user likes acoustic music and the song is acoustic enough, it gets an extra 0.5 points.

The song with the highest total score is ranked first.

When genre bonus was cut in half (from 2.0 to 1.0 points), genre alone could not dominate the result. The energy bonus was doubled in range (from a max of 1.5 to a max of 3.0 points) so that energy became the strongest single signal, rewarding songs that closely match the user's preferred intensity level.

---

## 4. Data  

The size of the dataset is 18 songs. 

The genres included in the catalog are: pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, classical, r&b, country, metal, latin, folk, and funk. Moods include: happy, chill, intense, relaxed, moody, focused, energetic, peaceful, romantic, nostalgic, angry, uplifting, groovy, and melancholic.

A key limitation is that several areas of musical taste are missing. There is no k-pop, no reggae, no blues, and no electronic subgenres beyond synthwave and EDM references in the profiles. Mood coverage is also uneven. For example, romantic, nostalgic, and groovy each appear in only one song, so users with those preferences will rarely get a mood match.

---

## 5. Strengths  

The system works best for users with high-energy preferences. There are many high-energy songs in the catalog, so those users get strong matches across genre, mood, and energy at the same time.

The energy similarity component is the strongest part of the scoring. Because it can contribute up to 3 points, it consistently pulls songs that actually sound like what the user wants — even when genre or mood do not match.

The system's outputs are simple and less cluttered, making it easier and less overwhelming to use.

---

## 6. Limitations and Bias 

Of the 17 songs in the dataset, 9 have an energy level above 0.7, while only 5 fall below 0.4. This leads to a limitation in the system, where high-energy genres like rock, pop, metal, and EDM are more represented in the data than calm genres like ambient, classical, and folk. Because the energy similarity score rewards closeness to the user's target, a low-energy listener (for example, a user who prefers ambient or sleep music near energy 0.1) has far fewer songs that can score well on energy, and the songs that do appear near their target are also spread across unrelated genres and moods. During testing, the "Chill Lofi" profile consistently surfaced acoustic songs from non-lofi genres in its top 5 simply because they happened to sit near the right energy value, not because they were stylistically close. This means the system quietly delivers worse recommendations to users with quieter tastes, not because of a flaw in the scoring formula itself, but because the data it scores against was never balanced to represent them fairly. This leads to high bias, which would be problematic if implemented in a real product.

---

## 7. Evaluation  


Eight profiles were tested using the `src/main.py` file: three standard (High-Energy Pop, Chill Lofi, Deep Intense Rock) and five adversarial (Conflicting Energy+Mood, Impossible Genre, Neutral Energy, Acoustic+EDM Mismatch, Perfect-Score Bait). For each run, the goal was to check whether the top-ranked song felt like something a real listener would actually want, and whether the score reasons honestly explained the result. Some results I found interesting are:

High-Energy Pop vs. Chill Lofi: These two profiles are at opposite energy extremes and the results reflected that; uptempo pop at the top of one, quiet lofi at the top of the other. However, I found it surprising that Chill Lofi never matched on mood once. The user preference said "calm" but every lofi song in the catalog is labeled "chill." The system treated those as a complete mismatch even though they mean nearly the same thing to a real person.

Conflicting Energy+Mood vs. High-Energy Pop: Swapping mood from "happy" to "sad" reshuffled the top results, but the system still returned energetic, upbeat songs because no pop songs with a sad mood exist in the dataset. The mood signal never fired at all. The system had no way to say that there are no matches for the user's preferences and just quietly returned the wrong thing.

Impossible Genre vs. Neutral Energy: Both disable one major signal. Impossible Genre (k-pop) means the genre bonus never fires. Neutral Energy (target 0.5) means energy scores bunch together and barely separate songs. In both cases the middle rankings felt arbitrary. Small coincidences in the data determined third versus fifth place.

---

## 8. Future Work  

- The system should include mood synonym matching. For example, right now "calm" and "chill" are treated as completely different, even though they mean the same thing to most listeners. A simple lookup table of equivalent mood labels would fix a lot of missed matches.

- For better explanations, the system could also say when something did not match. Telling a user that no matches were found is more accurate than silently returning wrong results.

- More songs should be incorporated into the dataset, especially in underrepresented genres and moods, so that edge-case users have real options instead of accidental near-matches.

---

## 9. Personal Reflection  

Building this made me realize that representative data matters just as much as a good algorithm. The scoring logic can be well-designed, but if the dataset is unbalanced, some users will quietly be more favored than others.

The most surprising thing was how much the mood label mismatch (calm vs. chill) broke the Chill Lofi profile. Two words that feel identical to a human completely shut off a scoring signal. It made me think about how much hidden work goes into label consistency in real music platforms.

I now look at apps like Spotify or YouTube differently. When a recommendation feels slightly off, I suspect the issue is not always the algorithm; it is probably a missing or mismatched label somewhere in the data pipeline. The algorithm can only work with what it is given. Thus, human judgement matters when creating more diverse datasets and better recommendations while also considering tradeoffs in time and memory space.
