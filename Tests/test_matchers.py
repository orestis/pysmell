import unittest
from pysmell.matchers import (matchCaseSensitively, matchCaseInsensitively,
        matchCamelCased, matchSmartass, matchFuzzyCS, matchFuzzyCI, camelGroups)

class MatcherTest(unittest.TestCase):
    def testCamelGroups(self):
        def assertCamelGroups(word, groups):
            self.assertEquals(list(camelGroups(word)), groups.split())
        assertCamelGroups('alaMaKota', 'ala Ma Kota')
        assertCamelGroups('AlaMaKota', 'Ala Ma Kota')
        assertCamelGroups('isHTML', 'is H T M L')
        assertCamelGroups('ala_ma_kota', 'ala _ma _kota')

    def testMatchers(self):
        def assertMatches(base, word):
            msg = "should complete %r for %r with %s" % (base, word, testedFunction.__name__)
            uncurried = testedFunction(base)
            self.assertTrue(uncurried(word), msg +  "for the first time")
            self.assertTrue(uncurried(word), msg + "for the second time")
        def assertDoesntMatch(base, word):
            msg = "shouldn't complete %r for %r with %s" % (base, word, testedFunction.__name__)
            uncurried = testedFunction(base)
            self.assertFalse(uncurried(word), msg +  "for the first time")
            self.assertFalse(uncurried(word), msg + "for the second time")
        def assertStandardMatches():
            assertMatches('Ala', 'Ala')
            assertMatches('Ala', 'AlaMaKota')
            assertMatches('ala_ma_kota', 'ala_ma_kota')
            assertMatches('', 'AlaMaKota')
            assertDoesntMatch('piernik', 'wiatrak')
        def assertCamelMatches():
            assertMatches('AMK', 'AlaMaKota')
            assertMatches('aM', 'alaMaKota')
            assertMatches('aMK', 'alaMaKota')
            assertMatches('aMaKo', 'alaMaKota')
            assertMatches('alMaK', 'alaMaKota')
            assertMatches('a_ma_ko', 'ala_ma_kota')
            assertDoesntMatch('aleMbiK', 'alaMaKota')
            assertDoesntMatch('alaMaKotaIPsaIRybki', 'alaMaKota')

        testedFunction = matchCaseSensitively
        assertStandardMatches()
        assertDoesntMatch('ala', 'Alamakota')
        assertDoesntMatch('ala', 'Ala')

        testedFunction = matchCaseInsensitively
        assertStandardMatches()
        assertMatches('ala', 'Alamakota')
        assertMatches('ala', 'Ala')
        
        testedFunction = matchCamelCased
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('aMK', 'alaMaKota')
        assertDoesntMatch('almako', 'ala_ma_kota')
        assertDoesntMatch('almako', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')

        testedFunction = matchSmartass
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('amk', 'alaMaKota')
        assertMatches('AMK', 'alaMaKota')
        assertMatches('almako', 'ala_ma_kota')
        assertMatches('almako', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')

        testedFunction = matchFuzzyCS
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('aMK', 'alaMaKota')
        assertMatches('aaMKa', 'alaMaKota')
        assertDoesntMatch('almako', 'alaMaKota')
        assertDoesntMatch('amk', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')

        testedFunction = matchFuzzyCI
        assertStandardMatches()
        assertCamelMatches()
        assertMatches('aMK', 'alaMaKota')
        assertMatches('aaMKa', 'alaMaKota')
        assertMatches('almako', 'alaMaKota')
        assertMatches('amk', 'alaMaKota')
        assertDoesntMatch('alkoma', 'alaMaKota')


if __name__ == '__main__':
    unittest.main()
