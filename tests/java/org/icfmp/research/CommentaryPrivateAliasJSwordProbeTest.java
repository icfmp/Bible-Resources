package org.icfmp.research;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

import org.crosswire.jsword.book.Book;
import org.crosswire.jsword.book.BookData;
import org.crosswire.jsword.book.Books;
import org.crosswire.jsword.book.OSISUtil;
import org.crosswire.jsword.book.sword.SwordBookPath;
import org.crosswire.jsword.passage.Key;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 * Real pinned JSword engine exercise of a *temporary* full original-commentary
 * rebuild with source-proven index aliases. Never exports commentary words.
 * This is not Android GUI or publication acceptance.
 */
public final class CommentaryPrivateAliasJSwordProbeTest {
    private static Book commentary;
    private static List<String[]> aliases;

    private static String humanReference(String osis) {
        String[] parts = osis.split("\\.", -1);
        assertEquals("Original OSIS verse reference", 3, parts.length);
        return parts[0] + " " + parts[1] + ":" + parts[2];
    }

    @BeforeClass
    public static void loadOnlyPrivateVerifiedCandidate() throws Exception {
        String path = System.getenv("PRIVATE_COMMENTARY_JSWORD_ROOT");
        String id = System.getenv("PRIVATE_COMMENTARY_JSWORD_ID");
        String mapping = System.getenv("PRIVATE_COMMENTARY_JSWORD_ALIASES");
        assertNotNull("Only the separately verified private candidate is accepted", path);
        assertNotNull(id);
        assertNotNull(mapping);
        assertTrue("Only a reviewed isolated module identity is tested",
                   id.matches("[A-Za-z][A-Za-z0-9_]{1,39}"));
        File root = new File(path).getCanonicalFile();
        assertTrue(root.isDirectory());
        assertTrue("Do not use an installed global SWORD module",
                   root.getPath().contains("commentary-source-native-")
                   && root.getPath().contains("complete-original-private-candidate"));
        assertTrue(new File(root, "mods.d/" + id.toLowerCase(java.util.Locale.ROOT)
                            + ".conf").isFile());
        aliases = new ArrayList<>();
        for (String row : mapping.split(";", -1)) {
            String[] pair = row.split("\\|", -1);
            assertEquals("Each alias must have an original linked master", 2, pair.length);
            assertTrue(pair[0].matches("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*"));
            assertTrue(pair[1].matches("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*"));
            assertNotEquals(pair[0], pair[1]);
            assertEquals("Alias must stay in the same original chapter",
                         pair[0].substring(0, pair[0].lastIndexOf('.')),
                         pair[1].substring(0, pair[1].lastIndexOf('.')));
            aliases.add(pair);
        }
        assertTrue("A bounded, source-driven alias set is required",
                   aliases.size() >= 1 && aliases.size() <= 12);
        SwordBookPath.setAugmentPath(new File[] {root});
        commentary = Books.installed().getBook(id);
        assertNotNull("JSword cannot load the private full-commentary candidate", commentary);
        assertEquals(id, commentary.getInitials());
    }

    @Test
    public void newAliasAndOriginalMasterAreBothAddressable() throws Exception {
        for (String[] pair : aliases) {
            Key target = commentary.getKey(humanReference(pair[0]));
            Key master = commentary.getKey(humanReference(pair[1]));
            assertNotNull(target);
            assertNotNull(master);
            assertEquals("The canonical target address was altered", pair[0], target.getOsisRef());
            assertEquals("The original master address was altered", pair[1], master.getOsisRef());
            assertTrue("New canonical alias not occupied for JSword", commentary.contains(target));
            assertTrue("Unchanged original commentary master not occupied for JSword",
                       commentary.contains(master));
            assertNotNull(commentary.getRawText(target));
            assertTrue("New alias contains no actual commentary prose",
                       commentary.getRawText(target).trim().length() >= 100);
        }
    }

    @Test
    public void sourceLinkedAliasAndMasterRenderSameSubstantialCanonicalProse() throws Exception {
        for (String[] pair : aliases) {
            Key target = commentary.getKey(humanReference(pair[0]));
            Key master = commentary.getKey(humanReference(pair[1]));
            String newText = OSISUtil.getCanonicalText(
                new BookData(commentary, target).getOsisFragment());
            String originalText = OSISUtil.getCanonicalText(
                new BookData(commentary, master).getOsisFragment());
            assertNotNull(newText);
            assertNotNull(originalText);
            String normalizedNew = newText.replaceAll("\\s+", " ").trim();
            String normalizedOld = originalText.replaceAll("\\s+", " ").trim();
            assertTrue("JSword dropped the substantive original section",
                       normalizedOld.length() >= 100);
            assertEquals("JSword renders changed words for the new index alias",
                         normalizedOld, normalizedNew);
        }
    }
}
