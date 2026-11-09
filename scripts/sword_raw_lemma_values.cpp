// Read only <w lemma> or <reference osisRef> attributes from stable SWORD
// raw entries. The mode determines which tag and attribute are audited.
// Scripture words, raw note bodies and entire OSIS fragments are never emitted.
// The record format is UTF-8: source-book-OSIS-ID<TAB>lemma-attribute<LF>.
// Each input line: normal-reader-key<TAB>source-book-OSIS-ID<TAB>0-or-1-intro.
// All files remain temporary and are never uploaded as CI artifacts.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <fstream>
#include <iostream>
#include <regex>
#include <string>

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    sword::SWMgr manager;
    sword::SWModule *module = manager.getModule(argv[1]);
    if (!module) return 3;
    auto *key = dynamic_cast<sword::VerseKey*>(module->getKey());
    if (!key) return 4;
    key->setIntros(true);
    key->setAutoNormalize(false);
    std::ifstream refs(argv[2]);
    if (!refs) return 5;
    std::ofstream output(argv[3], std::ios::binary | std::ios::trunc);
    if (!output) return 6;
    const std::string mode(argv[4]);
    const bool reference_mode = mode == "--reference-targets-only";
    if (!reference_mode && mode != "--word-lemmas-only") return 7;

    const std::regex selected_tag(reference_mode
        ? R"mark(<reference\b([^>]*)>)mark"
        : R"mark(<w\b([^>]*)>)mark");
    const std::regex selected_attr(reference_mode
        ? R"mark(\bosisRef\s*=\s*(["'])(.*?)\1)mark"
        : R"mark(\blemma\s*=\s*(["'])(.*?)\1)mark");
    const std::regex selected_name(reference_mode
        ? R"mark(\bosisRef\b)mark"
        : R"mark(\blemma\b)mark");
    std::string row;
    size_t entries = 0;
    size_t markers = 0;
    while (std::getline(refs, row)) {
        const auto first = row.find('\t');
        const auto second = first == std::string::npos ? first : row.find('\t', first + 1);
        if (first == std::string::npos || second == std::string::npos
            || row.find('\t', second + 1) != std::string::npos) return 8;
        const std::string ref = row.substr(0, first);
        const std::string book = row.substr(first + 1, second - first - 1);
        const std::string kind = row.substr(second + 1);
        if (ref.empty() || ref.size() > 120 || book.empty() || book.size() > 30
            || book.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") != std::string::npos
            || (kind != "0" && kind != "1")) return 9;
        *key = ref.c_str();
        if ((kind == "1" && key->getVerse() != 0)
            || (kind == "0" && key->getVerse() == 0)) return 10;
        const char *raw = module->getRawEntry();
        if (!raw) return 11;
        const std::string xml(raw);
        for (auto it = std::sregex_iterator(xml.begin(), xml.end(), selected_tag);
             it != std::sregex_iterator(); ++it) {
            const std::string attrs = (*it)[1].str();
            std::string value;
            auto match_begin = std::sregex_iterator(attrs.begin(), attrs.end(), selected_attr);
            auto match_end = std::sregex_iterator();
            if (match_begin != match_end) {
                value = (*match_begin)[2].str();
                if (++match_begin != match_end) return 12; // duplicate attributes
            } else if (std::regex_search(attrs, selected_name)) {
                return 13; // unknown quoting/unsupported lemma syntax
            }
            if (value.find('\t') != std::string::npos || value.find('\n') != std::string::npos
                || value.find('\r') != std::string::npos) return 14;
            output << book << '\t' << value << '\n';
            if (++markers > 5000000) return 15;
        }
        if (++entries > 150000) return 16;
    }
    if (!refs.eof() || entries == 0 || markers == 0 || !output.good()) return 17;
    return 0;
}
