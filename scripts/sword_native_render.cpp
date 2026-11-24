// Generic complete stable-SWORD Bible rendering audit; metadata only.
// The default Off mode is a strict gate. Enabled modes are separate evidence.
#include <sword/swmgr.h>
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
    if (argc != 3 || !std::regex_match(std::string(argv[1]),
        std::regex("[A-Za-z][A-Za-z0-9_]{0,79}")) ||
        !std::regex_match(std::string(argv[2]), std::regex("[1-9][0-9]{0,5}"))) return 2;
    const unsigned long expected = std::stoul(argv[2]);
    sword::SWMgr mgr;
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
                    if (html.find("<reference")!=std::string::npos ||
                        html.find("</reference")!=std::string::npos ||
                        html.find("osisRef=")!=std::string::npos ||
                        html.find("&lt;reference")!=std::string::npos ||
                        html.find("<note")!=std::string::npos ||
                        html.find("&lt;note")!=std::string::npos) ++rendered_leaks[i];
                }
                ++checked;
            }
        }
        key.increment();
    }
    for (unsigned i=0;i<names.size();++i)
        std::cout<<"NATIVE_RENDER {\"mode\":\""<<names[i]<<"\",\"checked\":"<<checked
                 <<",\"plain_leaks\":"<<plain_leaks[i]<<",\"rendered_osis_leaks\":"<<rendered_leaks[i]
                 <<",\"plain_changed_from_default\":"<<changed[i]<<",\"option_state_verified\":true}\n";
    // A known optional-mode stripText limitation is not silently fixed by
    // deleting valid authorial OSIS annotations. Keep it visible and separate.
    return checked==expected && plain_leaks[0]==0 && rendered_leaks[0]==0 ? 0 : 9;
}
