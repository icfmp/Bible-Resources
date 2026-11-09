// Read-only inventory of stable SWORD's note entry-attribute storage.
// Input: reader-key<TAB>OSIS-book-id<TAB>intro-flag.
// Output: book<TAB>raw-note-tags<TAB>swordFootnote-refs<TAB>
//         entry-Footnote-records<TAB>nonempty-entry-bodies
// No Scripture or note words, callouts or raw XML leave this process.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <sword/swbuf.h>
#include <fstream>
#include <regex>
#include <string>
#include <iostream>

int main(int argc, char **argv) {
    if (argc != 5 || std::string(argv[4]) != "--note-attributes-only") return 2;
    sword::SWMgr manager;
    sword::SWModule *module = manager.getModule(argv[1]);
    if (!module) return 3;
    auto *key = dynamic_cast<sword::VerseKey*>(module->getKey());
    if (!key) return 4;
    key->setIntros(true);
    key->setAutoNormalize(false);
    module->setProcessEntryAttributes(true);
    std::ifstream refs(argv[2]);
    std::ofstream output(argv[3], std::ios::trunc);
    if (!refs || !output) return 5;
    const std::regex opening(R"mark(<note\b)mark");
    const std::regex footnote(R"mark(\bswordFootnote\s*=\s*(["'])(.*?)\1)mark");
    std::string row;
    size_t entries = 0;
    while (std::getline(refs, row)) {
        auto a = row.find('\t');
        auto b = a == std::string::npos ? a : row.find('\t', a + 1);
        if (a == std::string::npos || b == std::string::npos
            || row.find('\t', b + 1) != std::string::npos) return 6;
        const std::string ref = row.substr(0, a);
        const std::string book = row.substr(a + 1, b - a - 1);
        const std::string kind = row.substr(b + 1);
        if (ref.empty() || ref.size() > 120 || book.empty() || book.size() > 30
            || book.find_first_not_of("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
               != std::string::npos
            || (kind != "0" && kind != "1")) return 7;
        *key = ref.c_str();
        if ((kind == "1" && key->getVerse() != 0)
            || (kind == "0" && key->getVerse() == 0)) return 8;
        const char *raw = module->getRawEntry();
        if (!raw) return 9;
        const std::string xml(raw);
        const size_t opens = static_cast<size_t>(
            std::distance(std::sregex_iterator(xml.begin(),xml.end(),opening),
                          std::sregex_iterator()));
        const size_t refs_count = static_cast<size_t>(
            std::distance(std::sregex_iterator(xml.begin(),xml.end(),footnote),
                          std::sregex_iterator()));
        // Force SWORD's standard option filters to materialize its own note
        // body store. The rendered Scripture result is deliberately discarded.
        (void) module->renderText();
        const auto &attributes = module->getEntryAttributes();
        size_t records = 0, with_body = 0;
        auto section = attributes.find(sword::SWBuf("Footnote"));
        if (section != attributes.end()) {
            for (const auto &entry : section->second) {
                ++records;
                const auto body = entry.second.find(sword::SWBuf("body"));
                if (body != entry.second.end() && body->second.size() > 0)
                    ++with_body;
            }
        }
        output << book << '\t' << opens << '\t' << refs_count << '\t'
               << records << '\t' << with_body << '\n';
        if (++entries > 150000) return 10;
    }
    if (!refs.eof() || entries == 0 || !output.good()) return 11;
    return 0;
}
