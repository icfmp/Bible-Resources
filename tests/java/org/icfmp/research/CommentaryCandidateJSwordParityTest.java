package org.icfmp.research;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

import org.crosswire.jsword.book.Book;
import org.crosswire.jsword.book.BookData;
import org.crosswire.jsword.book.Books;
import org.crosswire.jsword.book.OSISUtil;
import org.crosswire.jsword.book.sword.SwordBookPath;
import org.crosswire.jsword.passage.Key;
import org.jdom2.Content;
import org.jdom2.Element;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Generic second-engine SWORD zCom commentary acceptance against independently
 * native-read original K keys and SHA-pinned link target witnesses.
 *
 * The module is produced in a disposable CI SWORD_PATH. This is an actual
 * AndBible-pinned JSword ENGINE check, NOT AndBible Android/UI certification.
 * No authorial prose, original labels, rendered fragments or raw targets
 * are printed or committed.
 */
public final class CommentaryCandidateJSwordParityTest {
    private static Book commentary;
    private static List<String> samples;
    private static String[] witnesses;

    @BeforeClass
    public static void onlyReadExplicitPrivateCandidate() throws Exception {
        String folder = System.getenv("CANDIDATE_JSWORD_PRIVATE_ROOT");
        String name = System.getenv("CANDIDATE_JSWORD_MODULE_ID");
        String keys = System.getenv("CANDIDATE_JSWORD_SAMPLES");
        String links = System.getenv("CANDIDATE_JSWORD_NATIVE_LINK_SHA256_WITNESSES");
        assertNotNull("Private input directory required", folder);
        assertNotNull("Exact candidate SWORD ID required", name);
        assertNotNull("Native validated commentary samples required", keys);
        assertNotNull("Native reference witnesses required", links);
        assertTrue("Invalid private commentary module ID",
                   name.matches("[A-Za-z][A-Za-z0-9_]{1,39}"));
        File root = new File(folder).getCanonicalFile();
        assertTrue("Must use existing private SWORD_PATH", root.isDirectory());
        assertTrue("Never read a globally installed commentary",
                   root.getPath().contains("mhcc-modern-rc-root"));
        assertTrue("Missing private candidate module configuration",
                   new File(root, "mods.d/" + name.toLowerCase(Locale.ROOT)
                            + ".conf").isFile());
        samples = Arrays.asList(keys.split(";", -1));
        witnesses = links.split(";", -1);
        assertTrue("At least seven independently native-read sample passages",
                   samples.size() >= 7 && samples.size() <= 20);
        assertTrue("Only 2-6 separately native-attested link specimens",
                   witnesses.length >= 2 && witnesses.length <= 6);
        for (String sample : samples) {
            assertTrue("Malformed native preselected sample",
                       sample.matches("[1-4]?[A-Za-z][A-Za-z0-9 ]{1,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}"));
        }
        SwordBookPath.setAugmentPath(new File[] { root });
        commentary = Books.installed().getBook(name);
        assertNotNull("Pinned JSword did not load real candidate zCom", commentary);
        assertEquals("Reader loaded another SWORD module", name,
                     commentary.getInitials());
    }

    @Test
    public void resolvesEveryIndependentlyVerifiedNativeSample() throws Exception {
        for (String ref : samples) {
            Key key = commentary.getKey(ref);
            assertNotNull("JSword did not parse an existing native K reference", key);
            assertTrue("JSword cannot address native-occupied commentary", commentary.contains(key));
            String raw = commentary.getRawText(key);
            assertNotNull("JSword returned null for authentic native commentary", raw);
            assertTrue("JSword returned empty real compiled commentary", raw.trim().length() >= 8);
        }
    }

    @Test
    public void rendersSubstantiveStructuredProseFromRealCompiledCandidate() throws Exception {
        int count = 0;
        for (String ref : samples) {
            Element osis = new BookData(commentary, commentary.getKey(ref)).getOsisFragment();
            assertNotNull("Actual JSword commentary OSIS fragment absent", osis);
            String text = OSISUtil.getCanonicalText(osis);
            assertNotNull("JSword did not render substantive commentary", text);
            assertTrue("JSword lost the commentary prose", text.trim().length() >= 20);
            count++;
        }
        assertEquals(samples.size(), count);
    }

    private static String sha256(String value) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(
            value.getBytes(StandardCharsets.UTF_8));
        StringBuilder out = new StringBuilder(64);
        for (byte b : digest) {
            out.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        }
        return out.toString();
    }

    @Test
    public void preservesExactNativeScriptureLinksThroughIndependentJavaDecoder() throws Exception {
        int read = 0;
        for (String witness : witnesses) {
            String[] parts = witness.split("\\|", -1);
            assertEquals("Native link witness contains key and hashed targets", 2, parts.length);
            assertTrue("Untrusted native reference key",
                parts[0].matches("[1-4]?[A-Za-z][A-Za-z0-9 ]{1,35} [1-9][0-9]{0,2}:[1-9][0-9]{0,2}"));
            List<String> expected = new ArrayList<>(Arrays.asList(parts[1].split(",", -1)));
            assertTrue("Native link witness must contain original targets",
                       expected.size() >= 1 && expected.size() <= 256);
            for (String h : expected) {
                assertTrue("Invalid native source-linked target hash", h.matches("[a-f0-9]{64}"));
            }
            Collections.sort(expected);
            Key key = commentary.getKey(parts[0]);
            assertNotNull(key);
            assertTrue("Authentic link-bearing K missing", commentary.contains(key));
            Element osis = new BookData(commentary, key).getOsisFragment();
            assertNotNull(osis);
            List<String> observed = new ArrayList<>();
            if ("reference".equals(osis.getName())) {
                String target = osis.getAttributeValue("osisRef");
                if (target != null) observed.add(sha256(target));
            }
            for (Content child : osis.getDescendants()) {
                if (child instanceof Element) {
                    Element element = (Element) child;
                    if ("reference".equals(element.getName())) {
                        String target = element.getAttributeValue("osisRef");
                        if (target != null) observed.add(sha256(target));
                    }
                }
            }
            Collections.sort(observed);
            assertEquals("JSword changed or dropped native K Scripture reference targets",
                         expected, observed);
            read++;
        }
        assertEquals(witnesses.length, read);
    }

    @Test
    public void preservesDistinctJudgesAndJudeBookIdentities() throws Exception {
        Key judges = commentary.getKey("Judges 1:1");
        Key jude = commentary.getKey("Jude 1:1");
        assertNotNull(judges);
        assertNotNull(jude);
        assertNotEquals("JSword conflated unrelated canonical book addresses",
                        judges.getOsisRef(), jude.getOsisRef());
    }
}
