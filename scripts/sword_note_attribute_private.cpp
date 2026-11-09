// Private-only readout of the stock SWORD "Footnote" entry attributes.
// Read-only: dumps HEX-encoded footnote attributes to a temporary file;
// never prints Scripture or note texts, and never creates a CI artifact.
// Input rows: reader-key<TAB>osis-book-id<TAB>intro-flag
// Output rows: osis-book-id<TAB>reader-key<TAB>note-id-HEX<TAB>
//              attribute-name-HEX<TAB>attribute-value-HEX
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <sword/swbuf.h>
#include <fstream>
#include <string>
#include <iostream>

static std::string hex(const std::string &input) {
    static const char *alphabet="0123456789abcdef";
    std::string output;
    output.reserve(input.size()*2);
    for (unsigned char c:input) {
        output.push_back(alphabet[c >> 4]);
        output.push_back(alphabet[c & 15]);
    }
    return output;
}

int main(int argc, char **argv) {
    if (argc != 5 || std::string(argv[4]) != "--private-note-attributes")
        return 2;
    sword::SWMgr manager;
    sword::SWModule *module=manager.getModule(argv[1]);
    if (!module) return 3;
    auto *key=dynamic_cast<sword::VerseKey*>(module->getKey());
    if (!key) return 4;
    key->setIntros(true);
    key->setAutoNormalize(false);
    module->setProcessEntryAttributes(true);
    std::ifstream keys(argv[2]);
    std::ofstream output(argv[3],std::ios::binary | std::ios::trunc);
    if (!keys || !output) return 5;
    size_t entries=0, attributes=0, payload_bytes=0;
    std::string row;
    while (std::getline(keys,row)) {
        auto a=row.find('\t');
        auto b=a==std::string::npos ? a : row.find('\t',a+1);
        if (a==std::string::npos || b==std::string::npos
            || row.find('\t',b+1)!=std::string::npos) return 6;
        std::string ref=row.substr(0,a), book=row.substr(a+1,b-a-1),
                    intro=row.substr(b+1);
        if (ref.empty() || ref.size()>120 || book.empty() || book.size()>30
            || book.find_first_not_of("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")!=std::string::npos
            || (intro!="0" && intro!="1")) return 7;
        *key=ref.c_str();
        if ((intro=="1" && key->getVerse()!=0)
            || (intro=="0" && key->getVerse()==0)) return 8;
        (void)module->renderText();
        const auto &all=module->getEntryAttributes();
        const auto section=all.find(sword::SWBuf("Footnote"));
        if (section!=all.end()) {
            for (const auto &footnote:section->second) {
                const std::string note_id(footnote.first.c_str(),
                                          footnote.first.size());
                for (const auto &attribute:footnote.second) {
                    const std::string key_name(attribute.first.c_str(),
                                               attribute.first.size());
                    const std::string value(attribute.second.c_str(),
                                            attribute.second.size());
                    if (value.size()>100000) return 9;
                    payload_bytes+=value.size();
                    if (payload_bytes>40000000) return 10;
                    output<<book<<'\t'<<ref<<'\t'<<hex(note_id)<<'\t'
                          <<hex(key_name)<<'\t'<<hex(value)<<'\n';
                    if (++attributes>500000) return 11;
                }
            }
        }
        if (++entries>150000) return 12;
    }
    if (!keys.eof() || entries==0 || attributes==0 || !output.good()) return 13;
    return 0;
}
