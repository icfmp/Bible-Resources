package org.icfmp.research;

import java.io.File;
import java.util.Arrays;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Locale;
import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;

import org.jdom2.Content;

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

    private static String sha256Utf8(String value) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(
            value.getBytes(StandardCharsets.UTF_8)
        );
        StringBuilder hex = new StringBuilder(digest.length * 2);
        for (byte b : digest) {
            hex.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        }
        return hex.toString();
    }

    @Test
    public void preservesExactOriginalSourceOSISReferenceTargets() throws Exception {
        // The original target hashes are privately read from native,
        // SHA-pinned CrossWire SWORD raw keys before the Java test begins.
        // Neither their words nor hrefs are embedded in this test source.
        String original = System.getenv("COMMENTARY_JSWORD_REFERENCE_SHA256_WITNESSES");
        assertNotNull("Original native source-reference witnesses required", original);
        String[] specimens = original.split(";", -1);
        assertTrue("Two to six authentic original link-bearing keys required",
                   specimens.length >= 2 && specimens.length <= 6);
        for (String specimen : specimens) {
            String[] pair = specimen.split("\\|", -1);
            assertEquals("Source/target witness must contain exactly two parts", 2, pair.length);
            assertTrue("Source reference must be original SWORD key",
                       pair[0].matches("[1-4]?[A-Za-z][A-Za-z0-9 ]{1,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}"));
            String[] targetHashes = pair[1].split(",", -1);
            assertTrue("At least one authentic original link expected",
                       targetHashes.length >= 1 && targetHashes.length <= 256);
            List<String> expected = new ArrayList<>(Arrays.asList(targetHashes));
            for (String hash : expected) {
                assertTrue("Invalid original native reference fingerprint",
                           hash.matches("[a-f0-9]{64}"));
            }
            Collections.sort(expected);
            Key key = commentary.getKey(pair[0]);
            assertNotNull("Original source linked key not found in JSword", key);
            assertTrue("Original linked commentary entry not occupied", commentary.contains(key));
            Element root = new BookData(commentary, key).getOsisFragment();
            assertNotNull("JSword returned no actual OSIS fragment for reference key", root);
            List<String> observed = new ArrayList<>();
            if ("reference".equals(root.getName())) {
                String target = root.getAttributeValue("osisRef");
                if (target != null) {
                    observed.add(sha256Utf8(target));
                }
            }
            for (Content child : root.getDescendants()) {
                if (child instanceof Element) {
                    Element entry = (Element) child;
                    if ("reference".equals(entry.getName())) {
                        String target = entry.getAttributeValue("osisRef");
                        if (target != null) {
                            observed.add(sha256Utf8(target));
                        }
                    }
                }
            }
            Collections.sort(observed);
            // This is stronger than merely seeing a reference label: require
            // exact native source osisRef targets, with duplicate multiplicity.
            assertEquals("JSword lost or changed an original OSIS target", expected, observed);
        }
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
