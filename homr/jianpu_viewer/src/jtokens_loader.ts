/**
 * .jtokens file loader for the jianpu_viewer.
 *
 * Converts homr's 9-branch .jtokens format to the internal Score JSON
 * used by the Canvas renderer.
 *
 * Token format (9 fields per line):
 *   rhythm degree octave accidental articulation technique group dynamic lyric
 *
 * Legacy 6-field format is also supported (technique/group/dynamic auto-padded).
 */

import type { Score, Measure, Note, Dash, BarlineType, DiziTechnique } from './types';

/** Parse a single .jtokens line into 9 fields. */
function parseTokenLine(line: string): string[][] {
  return line.split('&').map(entry => {
    const parts = entry.trim().split(/\s+/);
    // Normalize to 9 fields
    if (parts.length < 6) {
      parts.push(...Array(6 - parts.length).fill('.'));
    }
    if (parts.length === 6) {
      // Legacy 6-field: insert technique, group, dynamic before lyric
      const lyric = parts[5];
      return [...parts.slice(0, 5), '.', '.', '.', lyric];
    }
    while (parts.length < 9) parts.push('.');
    if (parts.length > 9) {
      parts[8] = parts.slice(8).join(' ');
      parts = parts.slice(0, 9);
    }
    return parts;
  });
}

/** Map accidental token to JSON format. */
function accidentalTokenToJson(acc: string): 'sharp' | 'flat' | 'natural' | undefined {
  if (acc === '#') return 'sharp';
  if (acc === 'b') return 'flat';
  if (acc === 'N') return 'natural';
  return undefined;
}

/** Map technique token to JSON DiziTechnique. */
function techniqueTokenToJson(tech: string): DiziTechnique | undefined {
  if (tech === '.' || tech === '_') return undefined;
  if (tech === 'huayin_up') return { type: 'huayin', slideDirection: 'up' };
  if (tech === 'huayin_down') return { type: 'huayin', slideDirection: 'down' };
  return { type: tech as DiziTechnique['type'] };
}

/** Map barline token to JSON barline type. */
function barlineTokenToJson(rhythm: string): BarlineType {
  const map: Record<string, BarlineType> = {
    barline: 'single',
    doublebarline: 'double',
    bolddoublebarline: 'end',
    repeatStart: 'repeat-start',
    repeatEnd: 'repeat-end',
  };
  return map[rhythm] || 'single';
}

/** Duration in quarter-note units from kern string. */
function kernToDuration(kern: string): { duration: number; dot: number } {
  const isGrace = kern.includes('G');
  if (isGrace) kern = kern.replace('G', '');

  let i = 0;
  while (i < kern.length && kern[i].match(/\d/)) i++;
  const baseStr = kern.slice(0, i);
  const rest = kern.slice(i);
  const base = baseStr ? parseInt(baseStr) : 4;
  const dots = rest.split('.').length - 1;

  const durMap: Record<number, number> = {
    1: 4, 2: 2, 4: 1, 8: 0.5, 16: 0.25, 32: 0.125, 64: 0.0625,
  };
  let dur = durMap[base] || 1;

  let add = dur / 2;
  for (let d = 0; d < dots; d++) {
    dur += add;
    add /= 2;
  }

  return { duration: dur, dot: dots };
}

/**
 * Parse .jtokens text into a Score object.
 */
export function parseJtokensToScore(text: string, title: string = ''): Score {
  const lines = text.split('\n').filter(l => l.trim() && !l.trim().startsWith('#'));

  let key = 'C';
  let timeSignature = { numerator: 4, denominator: 4 };
  let tempo: number | undefined;

  const measures: Measure[] = [];
  let currentNotes: (Note | Dash)[] = [];
  let currentBarline: BarlineType = 'single';

  // Group tracking
  let tieActive = false;
  let slurActive = false;
  let tripletActive = false;
  let tieId = 0;
  let slurId = 0;
  let tripletId = 0;

  for (const line of lines) {
    const entries = parseTokenLine(line);

    for (const parts of entries) {
      const [rhythm, degree, octave, accidental, articulation, technique, group, dynamic, lyric] = parts;

      // Key signature
      if (rhythm.startsWith('jkey_')) {
        key = rhythm.slice(5);
        continue;
      }

      // Time signature
      if (rhythm.startsWith('jtime_')) {
        const m = rhythm.slice(6).match(/(\d+)_(\d+)/);
        if (m) {
          timeSignature = { numerator: parseInt(m[1]), denominator: parseInt(m[2]) };
        }
        continue;
      }

      // Tempo
      if (rhythm.startsWith('jtempo_')) {
        tempo = parseInt(rhythm.slice(7));
        continue;
      }

      // Chord marker
      if (rhythm === 'chord') continue;

      // Newline
      if (rhythm === 'newline') {
        // End current measure
        if (currentNotes.length > 0) {
          measures.push({ notes: currentNotes, barline: currentBarline });
          currentNotes = [];
          currentBarline = 'single';
        }
        continue;
      }

      // Barline
      if (rhythm.includes('barline') || rhythm.includes('repeat') || rhythm.includes('volta')) {
        currentBarline = barlineTokenToJson(rhythm);
        measures.push({ notes: currentNotes, barline: currentBarline });
        currentNotes = [];
        currentBarline = 'single';
        continue;
      }

      // Dash
      if (rhythm === 'dash') {
        currentNotes.push({ type: 'dash', duration: 1 });
        continue;
      }

      // Note or rest
      if (rhythm.startsWith('note') || rhythm.startsWith('rest')) {
        const isRest = rhythm.startsWith('rest');
        const kern = rhythm.replace(/^(note|rest)_/, '');
        const { duration, dot } = kernToDuration(kern);

        const pitch = isRest ? 0 : (parseInt(degree) || 0);
        const oct = parseInt(octave) || 0;
        const acc = accidentalTokenToJson(accidental);

        const note: Note = {
          pitch: pitch as Note['pitch'],
          octave: oct as Note['octave'],
          duration,
          dot: dot as Note['dot'],
        };

        if (acc) note.accidental = acc;
        if (technique !== '.' && technique !== '_') {
          const tech = techniqueTokenToJson(technique);
          if (tech) note.techniques = [tech];
        }

        // Articulation
        if (articulation === 'accent') note.accent = true;
        else if (articulation === 'tenuto') note.tenuto = true;
        else if (articulation === 'fermata') note.fermata = true;
        else if (articulation === 'staccato') note.staccato = true;
        else if (articulation === 'sf' || articulation === 'sfp' || articulation === 'fp') {
          note.forceAccent = articulation as Note['forceAccent'];
        }

        // Group (tie/slur/triplet)
        if (group === 'tie_start') {
          tieId++;
          note.tieId = `tie_${tieId}`;
          tieActive = true;
        } else if (group === 'tie_cont' && tieActive) {
          note.tieId = `tie_${tieId}`;
        } else if (group === 'tie_end' && tieActive) {
          note.tieId = `tie_${tieId}`;
          tieActive = false;
        }

        if (group === 'slur_start') {
          slurId++;
          note.slurId = `slur_${slurId}`;
          slurActive = true;
        } else if (group === 'slur_cont' && slurActive) {
          note.slurId = `slur_${slurId}`;
        } else if (group === 'slur_end' && slurActive) {
          note.slurId = `slur_${slurId}`;
          slurActive = false;
        }

        if (group === 'triplet_start') {
          tripletId++;
          note.tripletId = `triplet_${tripletId}`;
          tripletActive = true;
        } else if (group === 'triplet_cont' && tripletActive) {
          note.tripletId = `triplet_${tripletId}`;
        } else if (group === 'triplet_end' && tripletActive) {
          note.tripletId = `triplet_${tripletId}`;
          tripletActive = false;
        }

        // Dynamic
        if (dynamic !== '.' && dynamic !== '_') {
          note.dynamic = dynamic;
        }

        // Lyric
        if (lyric !== '.' && lyric !== '_' && lyric !== '-') {
          note.lyric = lyric;
        }

        currentNotes.push(note);
        continue;
      }
    }
  }

  // Don't forget the last measure
  if (currentNotes.length > 0) {
    measures.push({ notes: currentNotes, barline: 'single' });
  }

  const score: Score = {
    key,
    timeSignature,
    measures,
  };

  if (title) score.title = title;
  if (tempo) score.tempo = tempo;

  return score;
}
