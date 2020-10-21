#include <iostream>
#include <string>
#include <map>
#include <vector>
#include <algorithm>
#include <set>
#include <functional>
#include <iomanip>




class Symbol{
    enum class Type{
        TERMINAL,
        NON_TERMINAL
    };

    private:
    Type _type;
    char _c;
    std::vector<std::string> _candidates;

    public:

    Symbol() {
        _c = '\0';
    }

    Symbol(char c){
        _type = Type::TERMINAL;
        _c = c;
    }

    Symbol(const Symbol & s) {
        _type = s._type;
        _c = s._c;
        _candidates = s._candidates;
    }

    void setAsNonTerminal(const std::string &p) {
        _type = Type::NON_TERMINAL;

        auto split = [](const std::string& s, char d) -> auto{
            std::vector<std::string> v;
            auto start = 0U;
            auto end = s.find(d);
            while(end != std::string::npos) {
                v.emplace_back(s.substr(start, end - start));
                start = end + 1;
                end = s.find(d, start);
            }
            v.emplace_back(s.substr(start, end));
            return v;
        };
        _candidates = split(p, '|');
    }

    auto isTerminal() const{
        return (_type == Type::TERMINAL);
    }

    auto getCandidates() const{
        return _candidates;
    }

    auto getChar() const{
        return _c;
    }

    void print() const{
        std::cout << "Char : " << getChar() << std::endl;
        std::cout << (isTerminal() ? "Terminal" : "Non-Terminal") << std::endl;

        for(size_t i = 0; _candidates.size() && i < _candidates.size() - 1; ++i) {
            std::cout << _candidates[i] << '|';
        }

        if(_candidates.size()) {
            std::cout << _candidates.back();
        }
    }
};

auto myunion(const auto& s1, const auto &s2) {
    std::remove_cvref_t<decltype(s1)> tmp;
    std::insert_iterator ins{tmp, tmp.begin()};
    std::set_union(s1.cbegin(), s1.cend(), s2.cbegin(), s2.cend(), ins);
    return tmp;
};

auto myintersec(const auto& s1, const auto &s2) {
    std::remove_cvref_t<decltype(s1)> tmp;
    std::insert_iterator ins{tmp, tmp.begin()};
    std::set_intersection(s1.cbegin(), s1.cend(), s2.cbegin(), s2.cend(), ins);
    return tmp;
};

std::map<char, Symbol> symsGen(const std::vector<std::string> & productions) {
    std::map<char, Symbol> smap;
    for(auto && x : productions) {
        auto pos = x.find("->");
        if(pos == std::string::npos) {
            throw std::string("can not find \"->\" in a production : ") + x;
        }

        if(pos != 1) {
            throw std::string("production format error, production : ") + x;
        }

        // process content at the left of "->"
        if(smap.find(x[0]) == smap.end()) {
            Symbol s(x[0]);
            s.setAsNonTerminal(x.substr(pos + 2));
            smap.emplace(x[0], s);
        } else {
            smap[x[0]].setAsNonTerminal(x.substr(pos + 2));
        }
        // process content at the right of "->"
        for(size_t i = pos + 2; i < x.size(); ++i) {
            if(smap.find(x[i]) == smap.end()) {
                if(x[i] == '|') {
                    continue;
                }
                Symbol tmp(x[i]);
                smap[x[i]] = tmp;
            }
        }
    }
    return smap;
}


std::map<char, Symbol> removeLeftRecur(const std::map<char, Symbol> & syms) {
    bool upper[26] = {false}, lower[26] = {false};
    for(auto && [x,y] : syms) {
        if(x >= 'a' && x <= 'z') {
            lower[x - 'a'] = true;
        }

        if(x >= 'A' && x <= 'Z') {
            upper[x - 'A'] = true;
        }
    }

    auto getNextUnusedChar = [upper, lower]() mutable -> char{
        for(int i = 0; i < 26; ++i) {
            if(!upper[i]) {
                upper[i] = true;
                return 'A' + i;
            }

            if(!lower[i]) {
                lower[i] = true;
                return 'a' + i;
            }
        }
        return 0;
    };
    

    // first step, rewrite the productions
    // ref : http://www.cs.nuim.ie/~jpower/Courses/Previous/parsing/node30.html
    auto ret1 = syms;

    std::map<char, int> order_map;
    std::vector<char> nonterminal_order;
    for(auto && [x,y] : syms) {
        if(!y.isTerminal()) {
            order_map[x] = nonterminal_order.size();
            nonterminal_order.push_back(x);
        }
    }

    std::vector<std::string> candidates;
    for(int i = 0; i < nonterminal_order.size(); ++i) {

        candidates.clear();

        auto && symbol = ret1.at(nonterminal_order[i]);

        bool replace_occur = false;

        for(auto && st : symbol.getCandidates()) {
            char leftchar = st[0];
            if(auto && lower_symbol = ret1.at(leftchar); !lower_symbol.isTerminal() && order_map.at(leftchar) < i) {
                replace_occur = true;
                std::string alpha = {st.begin() + 1, st.end()};
                for(auto && lst : lower_symbol.getCandidates()) {
                    if(lst[0] == '?') {
                        candidates.push_back(alpha);
                    } else {
                        candidates.push_back(lst + alpha);
                    }
                }
            } else {
                candidates.push_back(st);
            }
        }

        std::string nstr{""};

        for(auto && x : candidates) {
            nstr += x + '|';
        }
        nstr.pop_back();
        ret1[symbol.getChar()].setAsNonTerminal(nstr);
        if(replace_occur) {
            --i;
        }
    }

    // second step, remove direct left recursion
    auto ret2 = ret1;
     
    std::vector<std::string> alpha, beta;

    for(auto && [x,y] : ret1) {
        if(y.isTerminal()) {
            continue;
        }


        for(auto && st : y.getCandidates()) {
            if(st[0] == x) {
                alpha.push_back({st.begin() + 1, st.end()});
            } else {
                beta.push_back({st.begin(), st.end()});
            }
        }

        if(alpha.size()) {
            char nc = getNextUnusedChar();
            Symbol nsym{nc};
            std::string ostr{""}, nstr{""};

            for(auto && betastr : beta) {
                ostr += (betastr + nc) + "|";
            }
            ostr.pop_back();
            ret2[x].setAsNonTerminal(ostr);

            for(auto && alphastr : alpha) {
                nstr += (alphastr + nc) + "|";
            }
            nstr.push_back('?');
            nsym.setAsNonTerminal(nstr);
            ret2[nc] = nsym;
            alpha.clear();
        }
        beta.clear();
    }
    return ret2;

}

auto firstSetOfSentence(const std::string & s,
const std::map<char, Symbol> & syms,
const std::map<char, std::set<char> > & first,
const std::map<char, bool> & nullable) {
    std::set<char> ret;
    for(auto && x : s) {
        ret = myunion(ret , first.at(x));
        if(!nullable.at(x)) {
            break;
        }
    }
    return ret; 
}



bool checkLL(const std::map<char, Symbol> & syms, 
const std::map<char, std::set<char>> first,
const std::map<char, std::set<char>> follow,
const std::map<char, bool> nullable) {
        
    for(auto && [x,y] : syms) {
        if(nullable.at(x) && !syms.at(x).isTerminal()) {
            if(myintersec(first.at(x), follow.at(x)).size()) {
                #ifdef DEBUG
                std::cerr << "union of first follow " << x << std::endl;
                #endif
                return false;
            }
        }

        if(!y.isTerminal()) {
            auto && candidates = y.getCandidates();
            
            for(int i = 0; i < candidates.size(); ++i) {
                for(int j = i + 1; j < candidates.size(); ++j) {
                    auto s1 = firstSetOfSentence(candidates[i], syms, first, nullable);
                    auto s2 = firstSetOfSentence(candidates[j], syms, first, nullable);
                    if(myintersec(s1,s2).size()) {
                        #ifdef DEBUG
                        std::cerr << "union of two fist : " << candidates[i] << ','<< candidates[j] << std::endl;
                        #endif
                        return false;
                    }
                }
            }
        }
    }

    return true;
}


auto firstfollowSetGen(const std::map<char, Symbol> &smap, char start) {
    std::map<char, std::set<char>> first;
    std::map<char, std::set<char>> follow;
    std::map<char, bool> nullable;

    for(auto && [x,y] : smap) {
        if(y.isTerminal()) {
            std::set<char> tmp;
            tmp.insert(x);
            first[x] = tmp;
        } else {
            first[x] = {};
        }
        follow[x] = {};
        nullable[x] = false;
    }

    nullable['?'] = true;
    follow[start].emplace('#');

    

    bool flag = true;
    while(flag) {
        flag = false;
        for(auto && [x,y] : smap) {

            if(y.isTerminal()) {
                continue;
            }

            auto first_old_size = first[x].size();
            auto nullable_old_value = nullable[x];
            // for each production of x
            for(auto && p : y.getCandidates()) {
                auto pos = 0U;
                while(pos < p.size() && nullable[p[pos]]) {
                    first[x] = myunion(first[x], first[p[pos]]);
                    ++pos;
                }
                
                if(pos < p.size()) {
                    first[x] = myunion(first[x], first[p[pos]]);
                }else {
                    nullable[x] = true;
                }


                auto all = [&nullable](auto c, auto start, auto end){
                    for(auto i = start; i < end; ++i) {
                        if(!nullable[c[i]]) {
                            return false;
                        }
                    }
                    return true;
                };


                for(auto i = 0; i < p.size(); ++i) {
                    if(all(p, i+1, p.size())) {
                        auto old = follow[p[i+1]].size();
                        follow[p[i]] = myunion(follow[x], follow[p[i]]);
                        if(old != follow[p[i+1]].size()) {
                            flag = true;
                        }
                    }
                }

                for(auto i = 0; i < p.size() - 1; ++i) {
                    for(auto j = i + 1; j < p.size(); ++j) {
                        if(all(p, i+1, j)) {
                            auto old = follow[p[i]].size();
                            follow[p[i]] = myunion(follow[p[i]], first[p[j]]);
                            if(old != follow[p[i]].size()) {
                                flag = true;
                            }
                        }
                    }
                }
            }

            if(first_old_size != first[x].size() || nullable_old_value != nullable[x]) {
                flag = true;
            }

        }
    }
    for(auto && [x,y] : first) {
        y.erase('?');
    }
    for(auto && [x,y] : follow) {
        y.erase('?');
    }
    return std::make_tuple(first, follow, nullable);
}

auto removeRedundantSymbols(const std::map<char, Symbol> syms, char start) {
    std::map<char, bool> vis;
    std::vector<char> buf;
    std::map<char, Symbol> ret;

    buf.push_back(start);
    while(!buf.empty()) {
        char c = buf.back();
        buf.pop_back();
        if(vis[c]) {
            continue;
        }
        vis[c] = true;
        auto single_sym = syms.at(c);
        if(!single_sym.isTerminal()) {
            for(auto && st : single_sym.getCandidates()) {
                for(auto && x : st) {
                    if(x == '?') {
                        continue;
                    }
                    if(!syms.at(x).isTerminal()) {
                        buf.push_back(x);
                    }
                }
            }
        }
    }

    for(auto && [x,y] : syms) {
        if(y.isTerminal()) {
            ret[x] = y;
        } else {
            if(vis[x]) {
                ret[x] = y;
            }
        }
    }
    return ret;

}

auto predictTableGen(const std::map<char, Symbol> syms,const std::map<char, std::set<char>> first, const std::map<char, std::set<char>> follow,const std::map<char, bool> nullable) {
    std::map<char, std::map<char, std::string>> ret;
    for(auto && [x,y] : syms) {
        if(y.isTerminal()) {
            continue;
        } else {
            ret[x] = {};
        }

        if(nullable.at(x)) {
            ret[x]['#'] = '?';
        }

        for(auto && s : y.getCandidates()) {
            for(auto && c : first.at(s[0])) {
                ret[x][c] = s;
            }

            if(nullable.at(s[0])) {
                for(auto && c : follow.at(x)) {
                    ret[x][c] = s;
                }
            }
        }
    }

    return ret;
}


void predictiveAnalysis(const std::map<char, std::map<char, std::string>> table, const std::string & in,const char start) {
    std::string sym_stack;
    size_t input_pos = 0;
    sym_stack.push_back('#');
    sym_stack.push_back(start);
    auto input = in;
    input.push_back('#');

    std::string last_sym_stack = in;
    size_t last_input_pos = 0;

    auto pretty_print = [&last_sym_stack, &last_input_pos, &input](const std::string & p) {
        std::cout << last_sym_stack << '\t' << (input.c_str() + last_input_pos) << '\t' << p << std::endl;

    };

    auto error_print = [](const std::string & e1, const std::string & e2){
        std::cout << "ERROR" << '\t' << e1 << '\t' << e2 <<std::endl;
    };

    while(!sym_stack.empty() && input_pos != input.size()) {
        char c = input[input_pos];

        if(c == sym_stack.back()) {
            last_sym_stack = sym_stack;
            sym_stack.pop_back();
            last_input_pos = input_pos;
            input_pos++;
            pretty_print("GETNEXT()");
            continue;
        }


        if(table.find(sym_stack.back()) == table.cend()) {
            error_print("Not Found in Predictive Table", sym_stack.back() + std::string{", "} + c);
            return;
        }

        auto && subtable = table.at(sym_stack.back());
        if(subtable.find(c) == subtable.cend()) {
            // not found
            error_print("Not Found in Predictive Table", sym_stack.back() + std::string{", "} + c);
            return;
        } else {
            auto && p = subtable.at(c);
            std::string tmp = std::string{sym_stack.back()} + std::string{"->"} + p;
            last_sym_stack = sym_stack;
            sym_stack.pop_back();


            if(p[0] != '?')
            for(auto i = (long)(p.size() - 1); i >= 0; --i) {
                sym_stack.push_back(p[i]);
            }
            pretty_print(tmp);
        }
    }

    if(!sym_stack.empty()) {
        error_print("Symbol Stack not Empty", "Input String is empty");
    }

    if(input_pos != input.size() ) {
        error_print("Symbol Stack is empty", "Input String not empty");
    }
}




int main(void) {
    std::vector<std::string> productions;
    int n;
    std::cin >> n;
    --n;
    std::string tmp, sentence;
    std::cin >> tmp;
    productions.push_back(tmp);
    char start_char = tmp[0];
    while(n--) {
        std::cin >> tmp;
        productions.push_back(tmp);
    }
    std::cin >> sentence;

    auto syms = symsGen(productions);
    auto syms1 = removeLeftRecur(syms);
    auto syms2 = removeRedundantSymbols(syms1, start_char);
    auto [first, follow, nullable] = firstfollowSetGen(syms2, start_char);
    auto table = predictTableGen(syms2, first, follow, nullable);

#ifdef DEBUG
    for(auto && [x, y] : syms1) {
        y.print();
        std::cout << std::endl;
    }

    for(auto && [x, y] : first) {
        std::cout << "Frist set of " << x << ": ";
        for(auto && z : y) {
            std::cout << z << ", ";
        };
        std::cout << std::endl;
    }

    for(auto && [x, y] : follow) {
        std::cout << "follow set of " << x << ": ";
        for(auto && z : y) {
            std::cout << z << ", ";
        };
        std::cout << std::endl;
    }

    for(auto && [x,y] : nullable) {
        std::cout << "Nullable(\'" << x << "\') = " << y << std::endl;
    }


    for(auto && [x1, y1] : table) {
        for(auto && [x2, y2] : y1) {
            std::cout << "T(" << x1 << ", " << x2 << ") = " << y2 << std::endl;
        }
    }
#endif // DEBUG

    bool check = checkLL(syms2, first, follow, nullable);
    std::cout << "CHECK_START#\n";
    std::cout << check << '\n';
    std::cout << "CHECK_END#\n";


    std::cout <<"PRODUCTIONS_START#\n";
    for(auto && [x,y] : syms2) {
        if(!y.isTerminal()) {
            std::cout << x << "->";
            auto && candi = y.getCandidates();
            for(int i = 0; i < candi.size() - 1; ++i) {
                std::cout << candi[i] << '|';
            }
            std::cout << candi.back() << '\n';
        }
   }
    std::cout <<"PRODUCTIONS_END#\n";



    std::cout << "FIRST_START#\n";
    for(auto && [x, y] : first) {
        std::cout << x << ":";
        for(auto && z : y) {
            std::cout << z << ",";
        };
        std::cout << std::endl;
    }
    std::cout << "FIRST_END#\n";

    std::cout << "FOLLOW_START#\n";
    for(auto && [x, y] : follow) {
        std::cout << x << ": ";
        for(auto && z : y) {
            std::cout << z << ",";
        };
        std::cout << std::endl;
    }
    std::cout << "FOLLOW_END#\n";


    std::cout << "NULLABLE_START#\n";
    for(auto && [x,y] : nullable) {
        std::cout << x << ":" << y << std::endl;
    }
    std::cout << "NULLABLE_END#\n";



    std::cout << "TABLE_START#\n";
    for(auto && [x1, y1] : table) {
        for(auto && [x2, y2] : y1) {
            std::cout << "T(" << x1 <<", " << x2 << ") = " << x1 << " -> " << y2 << std::endl;
        }
    }
    std::cout << "TABLE_END#\n";

    std::cout << "PROCESS_START#\n";
    predictiveAnalysis(table, sentence, start_char);
    std::cout << "PROCESS_END#\n";
    return 0;
}