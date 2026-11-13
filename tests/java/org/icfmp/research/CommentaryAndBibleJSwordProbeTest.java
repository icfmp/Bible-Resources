package org.icfmp.research;

import java.io.File;
import java.util.Arrays;
import java.util.List;

import org.crosswire.jsword.book.Book;
import org.crosswire.jsword.book.BookData;
import org.crosswire.jsword.book.Books;
import org.crosswire.jsword.book.OSISUtil;
import org.crosswire.jsword.book.sword.SwordBookPath;
import org.crosswire.jsword.passage.Key;
import org.jdom2.Element;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Independent Android AndBible-stable JSword *engine* readback of one pinned
 * original SWORD commentary, not the Android application or its GUI.
 *
 * Inputs come only from a preflighted official SWORD archive installed in a
 * temporary directory. The original module data and metadata stay unchanged.
 * Do not print author's words, reference labels, rendered XML or notes.
 */
public final class CommentaryAndBibleJSwordProbeTest {
    private static Book commentary;
    private static List<String> sampledReferences;

    @BeforeClass
    public static void loadOnlyIsolatedOriginal() throws Exception {
        String rootPath = System.getenv("COMMENTARY_JSWORD_MODULE_ROOT");
        String moduleId = System.getenv("COMMENTARY_JSWORD_MODULE_ID");
        String input = System.getenv("COMMENTARY_JSWORD_SAMPLES");
        assertNotNull("Pinned private module directory required", rootPath);
        assertNotNull("Exact original module identity required", moduleId);
        assertNotNull("Real diatheke-checked sample references required", input);
        File root = new File(rootPath).getCanonicalFile();
        assertTrue("An isolated SWORD directory is required", root.isDirectory());
        assertTrue("Never read a global SWORD library",
                   root.getPath().contains("commentary-andbible-jsword-private-"));
        assertTrue("Exact original SWORD config missing",
                   new File(root, "mods.d/" + moduleId.toLowerCase(java.util.Locale.ROOT)
                            + ".conf").isFile());
        sampledReferences = Arrays.asList(input.split(";", -1));
        assertTrue("At least two independent real entries required",
                   sampledReferences.size() >= 2 && sampledReferences.size() <= 20);
        for (String reference : sampledReferences) {
            assertTrue("Invalid independent probe reference",
                       reference.matches("[1-4]?[A-Za-z][A-Za-z0-9 ]{1,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}"));
        }
        SwordBookPath.setAugmentPath(new File[] { root });
        commentary = Books.installed().getBook(moduleId);
        assertNotNull("The original CrossWire commentary is not visible to JSword", commentary);
        assertEquals("A different module was selected", moduleId, commentary.getInitials());
    }

    @Test
    public void readsActualOriginalNativeCommentaryEntries() throws Exception {
        int read = 0;
        for (String reference : sampledReferences) {
            Key key = commentary.getKey(reference);
            assertNotNull("JSword could not resolve a confirmed stock key", key);
            assertTrue("JSword could not locate an actually occupied stock slot",
                       commentary.contains(key));
            String raw = commentary.getRawText(key);
            assertNotNull("JSword returned no raw commentary", raw);
            assertTrue("JSword returned an unexpectedly small commentary entry",
                       raw.trim().length() >= 8);
            read++;
        }
        assertEquals(sampledReferences.size(), read);
    }

    @Test
    public void readsActualStructuredOSISFragmentsWithoutDroppingAllProse() throws Exception {
        int read = 0;
        for (String reference : sampledReferences) {
            Key key = commentary.getKey(reference);
            Element fragment = new BookData(commentary, key).getOsisFragment();
            assertNotNull("Original SWORD comment OSIS fragment absent", fragment);
            String prose = OSISUtil.getCanonicalText(fragment);
            assertNotNull("Structured commentary rendered to null", prose);
            assertTrue("Structured commentary had no substantive prose",
                       prose.trim().length() >= 8);
            read++;
        }
        assertEquals(sampledReferences.size(), read);
    }

    @Test
    public void distinguishesCanonicalJudgesAndJudeSourceBookKeys() throws Exception {
        // This is a *reader key mapping* check. It does not rewrite or
        // validate a conflicting CCEL ThML scripCom annotation.
        Key judges = commentary.getKey("Judges 1:1");
        Key jude = commentary.getKey("Jude 1:1");
        assertNotNull(judges);
        assertNotNull(jude);
        assertNotEquals("A distinct original book address was conflated",
                        judges.getOsisRef(), jude.getOsisRef());
    }
}
