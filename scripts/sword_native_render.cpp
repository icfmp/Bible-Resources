// Generic complete stable-SWORD Bible rendering audit; metadata only.
// The default Off mode is a strict gate. Enabled modes are separate evidence.
#include <sword/swmgr.h>
#include <sword/markupfiltmgr.h>
#include <cstdlib>
#include <memory>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <array>
#include <iostream>
#include <regex>
#include <string>

static bool leaked(const std::string& s) {
    for (const char* marker : {"<reference", "</reference", "osisRef=",
                               "&lt;reference", "&lt;/reference",
                               "<note", "</note", "&lt;note", "&lt;/note",
                               "<verse ", "</verse", "<seg ", "</seg",
                               "<milestone ", "<div ", "</div"}) {
        if (s.find(marker) != std::string::npos) return true;
    }
    return false;
}

static bool rendered_osis(const std::string& html) {
    // Do not treat valid generated HTML attributes or structural divs as
    // visible OSIS. Count unconverted or escaped OSIS element names only.
    for (const char* marker : {"<reference", "</reference", "&lt;reference",
                               "&lt;/reference", "<note", "</note", "&lt;note",
                               "&lt;/note", "<seg ", "</seg", "&lt;seg",
                               "<milestone ", "&lt;milestone"}) {
        if (html.find(marker) != std::string::npos) return true;
    }
    return false;
}

static bool set_option(sword::SWMgr& mgr, const char* name, const char* value) {
    mgr.setGlobalOption(name, value);
    const char* observed = mgr.getGlobalOption(name);
    return observed && std::string(observed) == value;
}

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--self-test") {
        if (!leaked("text <reference osisRef=\"Gen.1.1\">label</reference>") ||
            !leaked("&lt;reference&gt;") || !leaked("<note type=\"x\">") ||
            leaked("ordinary words and punctuation") ||
            leaked("an HTML link <a href=\"sword://Gen.1.1\">label</a>")) return 1;
        return 0;
    }
    if ((argc != 3 && argc != 4) || !std::regex_match(std::string(argv[1]),
        std::regex("[A-Za-z][A-Za-z0-9_]{0,79}")) ||
        !std::regex_match(std::string(argv[2]), std::regex("[1-9][0-9]{0,5}"))) return 2;
    const unsigned long expected = std::stoul(argv[2]);
    // renderText() without a markup manager returns internal markup, not HTML.
    // Explicitly request the standard SWORD HTMLHREF renderer.
    const char* root = std::getenv("SWORD_PATH");
    if (!root || !*root) return 11;
    sword::SWMgr mgr(root, true, new sword::MarkupFilterMgr(sword::FMT_HTMLHREF), false, false);
    std::unique_ptr<sword::SWMgr> previous;
    sword::SWModule* old = nullptr;
    if (argc == 4) {
        previous.reset(new sword::SWMgr(argv[3], true, new sword::MarkupFilterMgr(sword::FMT_HTMLHREF), false, false));
        old = previous->getModule(argv[1]);
        if (!old) return 12;
    }
    sword::SWModule* module = mgr.getModule(argv[1]);
    if (!module) return 3;
    const char* driver = module->getConfigEntry("ModDrv");
    if (!driver || (std::string(driver) != "RawText" && std::string(driver) != "zText")) return 4;
    const auto* module_key = dynamic_cast<const sword::VerseKey*>(module->getKey());
    if (!module_key) return 5;
    sword::VerseKey key;
    key.setVersificationSystem(module_key->getVersificationSystem());
    key.setIntros(true);
    key.setAutoNormalize(false);
    key = sword::TOP;
    const std::regex numbered("[1-4]?[A-Za-z][A-Za-z0-9]*\\.[1-9][0-9]*\\.[1-9][0-9]*");
    const std::array<const char*,4> names = {"default_off", "xref_on", "notes_on", "both_on"};
    const std::array<const char*,4> xrefs = {"Off", "On", "Off", "On"};
    const std::array<const char*,4> notes = {"Off", "Off", "On", "On"};
    std::array<unsigned long,4> plain_leaks{}, rendered_leaks{}, changed{};
    std::array<unsigned long,4> previous_plain_leaks{}, previous_rendered_leaks{}, plain_diff{}, html_diff{}, new_plain_leaks{}, new_html_leaks{};
    unsigned long visited=0, checked=0;
    while (!key.popError()) {
        if (++visited > 300000) return 6;
        if (module->hasEntry(&key)) {
            const std::string ref = key.getOSISRef();
            if (std::regex_match(ref, numbered)) {
                if (module->setKey(key)) return 7;
                const auto* positioned = dynamic_cast<const sword::VerseKey*>(module->getKey());
                if (!positioned || std::string(positioned->getOSISRef()) != ref ||
                    !module->hasEntry(positioned)) return 8;
                if (old && (!old->hasEntry(&key) || old->setKey(key))) return 13;
                std::string baseline;
                for (unsigned i=0;i<names.size();++i) {
                    if (!set_option(mgr,"Cross-references",xrefs[i]) ||
                        !set_option(mgr,"Footnotes",notes[i])) return 10;
                    const std::string plain=module->stripText();
                    const sword::SWBuf rendered=module->renderText();
                    if (i==0) baseline=plain;
                    else if (plain!=baseline) ++changed[i];
                    if (leaked(plain)) {
                        ++plain_leaks[i];
                        if (plain_leaks[i]<=12) std::cerr<<"Literal plain markup "<<names[i]<<" "<<ref<<"\n";
                    }
                    // Rendered HTML can legitimately contain structural divs.
                    const std::string html=rendered.c_str();
                    if (rendered_osis(html)) ++rendered_leaks[i];
                    if (old) {
                        // An older invalid/missing optional filter may not expose
                        // that option at all. Record output under the request.
                        previous->setGlobalOption("Cross-references", xrefs[i]);
                        previous->setGlobalOption("Footnotes", notes[i]);
                        const std::string old_plain = old->stripText();
                        const sword::SWBuf old_buffer = old->renderText();
                        const std::string old_html = old_buffer.c_str();
                        if (old_plain != plain) ++plain_diff[i];
                        if (old_html != html) ++html_diff[i];
                        if (leaked(old_plain)) ++previous_plain_leaks[i];
                        if (rendered_osis(old_html)) ++previous_rendered_leaks[i];
                        if (leaked(plain) && !leaked(old_plain)) ++new_plain_leaks[i];
                        if (rendered_osis(html) && !rendered_osis(old_html)) ++new_html_leaks[i];
                    }
                }
                ++checked;
            }
        }
        key.increment();
    }
    for (unsigned i=0;i<names.size();++i)
        std::cout<<"NATIVE_RENDER {\"mode\":\""<<names[i]<<"\",\"checked\":"<<checked
                 <<",\"plain_leaks\":"<<plain_leaks[i]<<",\"rendered_osis_leaks\":"<<rendered_leaks[i]
                 <<",\"plain_changed_from_default\":"<<changed[i]<<",\"option_state_verified\":true,\"render_format\":\"HTMLHREF\"}\n";
    if (old) for (unsigned i=0;i<names.size();++i)
        std::cout<<"PREVIOUS_RENDER_COMPARISON {\"mode\":\""<<names[i]<<"\",\"checked\":"<<checked
                 <<",\"previous_plain_leaks\":"<<previous_plain_leaks[i]
                 <<",\"previous_rendered_osis_leaks\":"<<previous_rendered_leaks[i]
                 <<",\"plain_different\":"<<plain_diff[i]<<",\"html_different\":"<<html_diff[i]
                 <<",\"new_plain_leaks\":"<<new_plain_leaks[i]<<",\"new_html_leaks\":"<<new_html_leaks[i]<<"}\n";
    // A known optional-mode stripText limitation is not silently fixed by
    // deleting valid authorial OSIS annotations. Keep it visible and separate.
    return checked==expected && plain_leaks[0]==0 && rendered_leaks[0]==0 ? 0 : 9;
}
