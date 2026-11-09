// Count lexical word markers preceding each raw SWORD note in every entry.
// Input: reader-key<TAB>osis-book-id<TAB>intro-flag.
// Output: book<TAB>reader-key<TAB>word-tags-outside-notes<TAB>
//         comma-separated-word-offsets-of-raw-note-start-tags
// No Scripture text, note text, XML fragments or identities are exported.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <fstream>
#include <string>
#include <regex>
#include <vector>
#include <iostream>

int main(int argc, char **argv) {
    if (argc!=5 || std::string(argv[4])!="--note-word-anchors-only") return 2;
    sword::SWMgr manager;
    sword::SWModule *module=manager.getModule(argv[1]);
    if (!module) return 3;
    auto *key=dynamic_cast<sword::VerseKey*>(module->getKey());
    if (!key) return 4;
    key->setIntros(true);
    key->setAutoNormalize(false);
    std::ifstream refs(argv[2]);
    std::ofstream output(argv[3],std::ios::trunc);
    if (!refs || !output) return 5;
    const std::regex tags(R"tag(<(/?)(w|note)\b([^>]*)>)tag");
    std::string row;
    size_t entries=0;
    while (std::getline(refs,row)) {
        const auto a=row.find('\t');
        const auto b=(a==std::string::npos)?a:row.find('\t',a+1);
        if (a==std::string::npos || b==std::string::npos
            || row.find('\t',b+1)!=std::string::npos) return 6;
        const std::string ref=row.substr(0,a);
        const std::string book=row.substr(a+1,b-a-1);
        const std::string intro=row.substr(b+1);
        if (ref.empty() || ref.size()>120 || book.empty() || book.size()>30
            || book.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
               != std::string::npos
            || (intro!="0" && intro!="1")) return 7;
        *key=ref.c_str();
        if ((intro=="1" && key->getVerse()!=0)
            || (intro=="0" && key->getVerse()==0)) return 8;
        const char *raw=module->getRawEntry();
        if (!raw) return 9;
        const std::string xml(raw);
        int word_count=0, note_depth=0;
        std::vector<int> anchors;
        for (auto it=std::sregex_iterator(xml.begin(),xml.end(),tags);
             it!=std::sregex_iterator();++it) {
            const bool end=(*it)[1].str()=="/";
            const std::string tag=(*it)[2].str();
            const std::string attrs=(*it)[3].str();
            const bool self_closing=!attrs.empty() &&
                attrs.find_last_not_of(" \n\r\t")!=std::string::npos &&
                attrs[attrs.find_last_not_of(" \n\r\t")]=='/';
            if (tag=="note") {
                if (end) {
                    if (note_depth<=0) return 10;
                    --note_depth;
                } else {
                    if (note_depth==0) anchors.push_back(word_count);
                    if (!self_closing) ++note_depth;
                }
            } else if (tag=="w" && !end && note_depth==0) {
                ++word_count;
            }
        }
        if (note_depth!=0) return 11;
        output<<book<<'\t'<<ref<<'\t'<<word_count<<'\t';
        for (size_t i=0;i<anchors.size();++i) {
            if (i) output<<',';
            output<<anchors[i];
        }
        output<<'\n';
        if (++entries>150000) return 12;
    }
    if (!refs.eof() || entries==0 || !output.good()) return 13;
    return 0;
}
