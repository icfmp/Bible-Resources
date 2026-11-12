package org.icfmp.research;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.Set;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.crosswire.jsword.book.Book;
import org.crosswire.jsword.book.BookData;
import org.crosswire.jsword.book.BookMetaData;
import org.crosswire.jsword.book.Books;
import org.crosswire.jsword.book.OSISUtil;
import org.crosswire.jsword.book.sword.SwordBookPath;
import org.crosswire.jsword.passage.Key;
import org.crosswire.jsword.passage.Verse;
import org.crosswire.jsword.versification.BibleBook;
import org.crosswire.jsword.versification.Versification;
import org.crosswire.jsword.versification.system.Versifications;
import org.jdom2.Element;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Executed ONLY against AndBible stable's exact pinned JSword submodule
 * (AndBible/and-bible production-1117, JSword 6ebd10a005fa...).
 *
 * It consumes the same temporary SWORD files already audited with native
 * SWORD; never downloads or distributes any biblical words.
 * Success here is an independent Java ENGINE test, not an Android UI test.
 */
public final class DarbyAndBibleJSwordProbeTest {
    private static final String MODULE = "JND2024RepairResearch";
    private static Book bible;

    @BeforeClass
    public static void loadOnlyPrivatePublisherCandidate() throws Exception {
        String where = System.getenv("DARBY_JSWORD_MODULE_ROOT");
        assertNotNull("Private SWORD test root is required", where);
        File root = new File(where).getCanonicalFile();
        assertTrue("Private SWORD root must be an existing directory", root.isDirectory());
        assertTrue("Exactly one private module config is required",
            new File(root, "mods.d/jnd2024repairresearch.conf").isFile());
        assertTrue("No permanent global SWORD directory may be used",
            where.contains("private-darby-repaired-sword-"));
        SwordBookPath.setAugmentPath(new File[] { root });
        bible = Books.installed().getBook(MODULE);
        assertNotNull("Exact corrected module is not available in AndBible JSword", bible);
        assertEquals(MODULE, bible.getInitials());
        assertEquals("Luther", bible.getBookMetaData().getProperty(BookMetaData.KEY_VERSIFICATION));
    }

    private static Element osis(String ref) throws Exception {
        Key key = bible.getKey(ref);
        assertTrue("JSword did not find authentic compiled entry " + ref, bible.contains(key));
        String raw = bible.getRawText(key);
        assertNotNull("JSword raw entry missing " + ref, raw);
        assertTrue("JSword returned an empty compiled entry " + ref, raw.trim().length() >= 4);
        Element result = new BookData(bible, key).getOsisFragment();
        assertNotNull("JSword failed to produce a structured OSIS fragment " + ref, result);
        return result;
    }

    private static void find(Element node, String name, List<Element> output) {
        if (node.getName().equals(name)) {
            output.add(node);
        }
        for (Element child : node.getChildren()) {
            find(child, name, output);
        }
    }

    private static List<Element> elements(Element node, String name) {
        List<Element> found = new ArrayList<>();
        find(node, name, found);
        return found;
    }

    private static boolean hasTarget(Element note, String exact) {
        for (Element ref : elements(note, "reference")) {
            if (exact.equals(ref.getAttributeValue("osisRef"))) {
                return true;
            }
        }
        return false;
    }

    @Test
    public void readsRealFrenchTextAcrossGenresAndBothTestaments() throws Exception {
        for (String ref : Arrays.asList(
                "Genesis 1:1", "Psalms 23:1", "Psalms 150:2",
                "Leviticus 8:15", "Ezekiel 4:11", "Matthew 23:13",
                "Acts 8:36", "Acts 15:33", "Romans 16:25",
                "Colossians 2:2", "Revelation 22:21")) {
            Element fragment = osis(ref);
            String plain = OSISUtil.getCanonicalText(fragment);
            assertNotNull("JSword canonical output null " + ref, plain);
            assertTrue("JSword canonical output empty or unreasonably short " + ref,
                       plain.trim().length() >= 6);
        }
    }

    @Test
    public void rendersRealSourceNotesAndRepairedWrongBookReference() throws Exception {
        Element fragment = osis("Romans 16:25");
        List<Element> notes = elements(fragment, "note");
        assertTrue("JSword dropped the original Romans note", notes.size() >= 1);
        boolean foundCorrected = false;
        for (Element note : notes) {
            if (hasTarget(note, "Col.2.2-Col.2.3")) {
                foundCorrected = true;
            }
            assertFalse("JSword still exposes the old wrong-book Colossians target",
                        hasTarget(note, "1Cor.2.2-1Cor.2.3"));
            assertFalse("JSword still exposes the old wrong-book Ephesians target",
                        hasTarget(note, "1Cor.5.32"));
        }
        assertTrue("JSword did not expose the actual corrected Colossians note destination",
                   foundCorrected);
    }

    @Test
    public void retainsTextualCriticalNotesWithoutDeadVerseTargets() throws Exception {
        for (String[] sample : new String[][] {
                {"Matthew 23:13", "Matt.23.14"},
                {"Acts 8:36", "Acts.8.37"},
                {"Acts 15:33", "Acts.15.34"},
        }) {
            Element fragment = osis(sample[0]);
            List<Element> notes = elements(fragment, "note");
            assertTrue("A textual-critical note disappeared " + sample[0], notes.size() >= 1);
            boolean readable = false;
            for (Element note : notes) {
                assertFalse("The omitted-verse dead machine target survived " + sample[1],
                            hasTarget(note, sample[1]));
                if (note.getValue().trim().length() >= 12) {
                    readable = true;
                }
            }
            assertTrue("The omitted-verse explanatory note became unreadable " + sample[0],
                       readable);
            Key omitted = bible.getKey(sample[1].replace('.', ' '));
            assertFalse("JSword exposes an intentionally absent verse as real " + sample[1],
                        bible.contains(omitted));
        }
    }

    @Test
    public void retainsReviewedInlineMeasurementNote() throws Exception {
        Element fragment = osis("Ezekiel 4:11");
        List<Element> notes = elements(fragment, "note");
        assertTrue("The Ezekiel authorial measurement note is not present", notes.size() > 0);
        boolean readable = false;
        for (Element note : notes) {
            if (note.getValue().trim().length() >= 15) {
                readable = true;
            }
        }
        assertTrue("JSword did not retain the authorial Ezekiel note text", readable);
    }

    @Test
    public void checksEveryAuthoredVerseThroughRealJswordIndexWithoutPhantomTexts() throws Exception {
        // JSword's scope may contain nominal versification slots and intros.
        // Those are not necessarily populated Bible verse entries. Compare
        // the actual .contains() result against the exact reviewed source keys
        // rather than assuming scope.getCardinality() equals source text count.
        String manifest = System.getenv("DARBY_JSWORD_ORIGINAL_KEYS");
        assertNotNull("Exact original index manifest is required", manifest);
        List<String> keys = Files.readAllLines(Paths.get(manifest), StandardCharsets.US_ASCII);
        assertEquals("Unverified authored verse reference manifest", 31166, keys.size());
        Versification luther = Versifications.instance().getVersification("Luther");
        assertNotNull("AndBible JSword does not support real Luther versification", luther);
        Set<String> expected = new HashSet<>();
        int missing = 0;
        for (String osis : keys) {
            assertTrue("Invalid authorial OSIS reference shape",
                       osis.matches("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*"));
            assertTrue("Duplicated source verse ID in JSword manifest", expected.add(osis));
            String[] parts = osis.split("\\.");
            BibleBook book = BibleBook.fromExactOSIS(parts[0]);
            assertNotNull("Unknown authorial OSIS book to AndBible JSword", book);
            Verse verse = new Verse(luther, book,
                    Integer.parseInt(parts[1]), Integer.parseInt(parts[2]));
            assertEquals("JSword changed a source OSIS verse address", osis, verse.getOsisRef());
            if (!bible.contains(verse)) missing++;
        }
        assertEquals("JSword cannot address authored source verses", 0, missing);
        int nominalScope = bible.getScope().getCardinality();
        int extraPopulated = 0;
        int unpopulatedScopeSlots = 0;
        for (Key candidate : bible.getScope()) {
            if (!(candidate instanceof Verse)) continue;
            Verse v = (Verse) candidate;
            if (v.getChapter() <= 0 || v.getVerse() <= 0) continue;
            if (!expected.contains(v.getOsisRef())) {
                if (bible.contains(v)) extraPopulated++;
                else unpopulatedScopeSlots++;
            }
        }
        System.out.println("JSWORD_SCOPE_CARDINALITY=" + nominalScope);
        System.out.println("JSWORD_SCOPE_EXTRA_POPULATED=" + extraPopulated);
        System.out.println("JSWORD_SCOPE_EMPTY_NOMINAL_SLOTS=" + unpopulatedScopeSlots);
        assertEquals("JSword reports numbered Bible entries absent from the authorial source",
                     0, extraPopulated);
    }

}
