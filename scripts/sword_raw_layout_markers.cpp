// Read-only stable SWORD structural layout marker probe (no Scripture output).
// Emits one tab-separated row per requested reader entry:
// book, key, p-start/end, title-start/end, lg-start/end, q-start/end.
// Logical start tags are counted once, while OSIS eID milestones are
// separately accounted for. Ordinary XML closing tags do not count as a
// second authored structure. No markup values or text are exported.
#include <sword/swmgr.h>
#include <sword/swmodule.h>
#include <sword/versekey.h>
#include <fstream>
#include <iostream>
#include <map>
#include <regex>
#include <string>
#include <vector>

int main(int argc, char **argv) {
    if (argc!=5) return 2;
    const std::string mode(argv[4]);
    const bool positions = mode=="--layout-start-word-positions-only";
    if (!positions && mode!="--layout-markers-only") return 2;
    sword::SWMgr manager;
    sword::SWModule *module=manager.getModule(argv[1]);
    if (!module) return 3;
    auto *key=dynamic_cast<sword::VerseKey*>(module->getKey());
    if (!key) return 4;
    key->setIntros(true);
    key->setAutoNormalize(false);
    std::ifstream source(argv[2]);
    std::ofstream destination(argv[3],std::ios::trunc);
    if (!source || !destination) return 5;
    const std::regex tags(R"tag(<([A-Za-z][A-Za-z0-9]*)\b([^>]*)>)tag");
    const std::regex sid(R"tag(\bsID\s*=)tag");
    const std::regex eid(R"tag(\beID\s*=)tag");
    // Released osis2mod replaces non-milestoneable <p> with
    // <div type="x-p" sID="..."/> and matching eID milestones.
    const std::regex paragraph_div(R"tag(\btype\s*=\s*(["'])(x-p|paragraph)\1)tag");
    std::string row;
    size_t entries=0;
    while (std::getline(source,row)) {
        const auto a=row.find('\t');
        const auto b=a==std::string::npos ? a : row.find('\t',a+1);
        if (a==std::string::npos || b==std::string::npos
            || row.find('\t',b+1)!=std::string::npos) return 6;
        const std::string ref=row.substr(0,a), book=row.substr(a+1,b-a-1),
                          intro=row.substr(b+1);
        if (ref.empty() || ref.size()>120 || book.empty() || book.size()>30
            || book.find_first_not_of("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
               !=std::string::npos
            || (intro!="0" && intro!="1")) return 7;
        *key=ref.c_str();
        if ((intro=="1" && key->getVerse()!=0)
            || (intro=="0" && key->getVerse()==0)) return 8;
        const char *raw=module->getRawEntry();
        if (!raw) return 9;
        const std::string xml(raw);
        std::map<std::string,unsigned> starts,ends;
        unsigned words=0;
        std::vector<std::string> events;
        for (auto it=std::sregex_iterator(xml.begin(),xml.end(),tags);
             it!=std::sregex_iterator();++it) {
            std::string tag=(*it)[1].str();
            const std::string attrs=(*it)[2].str();
            if (tag=="w") {
                if (++words>5000) return 13;
                continue;
            }
            if (tag=="div" && std::regex_search(attrs,paragraph_div)) tag="p";
            if (tag!="p" && tag!="title" && tag!="lg" && tag!="q") continue;
            const bool start=std::regex_search(attrs,sid);
            const bool end=std::regex_search(attrs,eid);
            if (start && end) return 10;
            if (end) ++ends[tag]; else {
                ++starts[tag];
                events.push_back(tag+":"+std::to_string(words));
                if (events.size()>5000) return 14;
            }
        }
        destination<<book<<'\t'<<ref;
        if (positions) {
            destination<<'\t'<<words<<'\t';
            for (size_t i=0;i<events.size();++i) {
                if (i) destination<<',';
                destination<<events[i];
            }
        } else {
            for (const char *tag:{"p","title","lg","q"}) {
                destination<<'\t'<<starts[tag]<<'\t'<<ends[tag];
            }
        }
        destination<<'\n';
        if (++entries>150000) return 11;
    }
    if (!source.eof() || entries==0 || !destination.good()) return 12;
    return 0;
}
