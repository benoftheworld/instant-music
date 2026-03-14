import { describe } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { formatAnswer } from '@/utils/formatAnswer';

class FormatAnswerTest extends BaseUtilTest {
  protected name = 'formatAnswer';

  run() {
    describe('formatAnswer', () => {
      this.testPlainText();
      this.testJsonArtistOnly();
      this.testJsonTitleOnly();
      this.testJsonArtistAndTitle();
      this.testJsonEmptyObject();
      this.testInvalidJson();
      this.testEmptyString();
    });
  }

  private testPlainText() {
    this.testPureFunction('retourne le texte brut tel quel', formatAnswer, [
      { input: 'Daft Punk', expected: 'Daft Punk' },
      { input: 'Some random text', expected: 'Some random text' },
    ]);
  }

  private testJsonArtistOnly() {
    this.testPureFunction(
      'extrait l\'artiste d\'un JSON',
      formatAnswer,
      [{ input: '{"artist":"Daft Punk"}', expected: 'Daft Punk' }],
    );
  }

  private testJsonTitleOnly() {
    this.testPureFunction(
      'extrait le titre d\'un JSON',
      formatAnswer,
      [{ input: '{"title":"Get Lucky"}', expected: 'Get Lucky' }],
    );
  }

  private testJsonArtistAndTitle() {
    this.testPureFunction(
      'combine artiste et titre',
      formatAnswer,
      [{ input: '{"artist":"Daft Punk","title":"Get Lucky"}', expected: 'Daft Punk - Get Lucky' }],
    );
  }

  private testJsonEmptyObject() {
    this.testPureFunction(
      'retourne le JSON brut pour un objet vide',
      formatAnswer,
      [{ input: '{}', expected: '{}' }],
    );
  }

  private testInvalidJson() {
    this.testPureFunction(
      'retourne le texte pour du JSON invalide',
      formatAnswer,
      [{ input: '{invalid json}', expected: '{invalid json}' }],
    );
  }

  private testEmptyString() {
    this.testPureFunction(
      'retourne une chaîne vide',
      formatAnswer,
      [{ input: '', expected: '' }],
    );
  }
}

new FormatAnswerTest().run();
