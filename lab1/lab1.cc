#include <iostream>
#include <vector>
#include <string>
#include <utility>
#include <limits>
#include <cctype>
#include <fstream>
#include <algorithm>

enum class TokenType {
    KEYWORD,
    IDENTIFIER,
    SEPARATOR,
    CONSTANT,
    ALG_OP,
    CMP_OP
};


struct Token {
    TokenType type;
    std::string st;
    int p;
};

template<typename T>
void input_stub(std::vector<T> &output, const std::string prompt) {
    if(!std::cin.good()) {
        std::cin.clear();
        std::cin.ignore(std::cin.rdbuf()->in_avail());
    }

    std::cout << prompt;
    T tmp;
    int n;
    std::cout << "\t firstly input the number of your inputs: ";
    std::cin >> n;

    while(std::cin >> tmp) {
        output.emplace_back(std::move(tmp));
        if(!(--n)) {
            return;
        }
    }
}


template<typename T>
auto is_in(const std::vector<T> &con, const T &val) {
    auto t = std::find(con.cbegin(), con.cend(), val);
    if(t == con.end()) {
        return int(-1);
    } else {
        return int(t - con.cbegin());
    }
}

auto is_in_first(const std::vector<std::string> &con, const char &val)->int {
    for(size_t i = 0; i < con.size(); ++i) {
        if(con[i].size() && con[i][0] == val) {
            return i;
        }
    }
    return -1;
}

bool read_constant(std::istream &is, std::string &out) {
    std::string tmp;
    bool has_dot = false;
    bool good = true;

    auto error_solve = [&is, &tmp]() {
         while(is.good()) {
            char t = is.peek();
            if(isdigit(t) || isalpha(t) || t == '.') {
                is >> t;
                tmp.push_back(t);
            } else {
                break;
            }
        }
    };

    while(is.good()) {
        char c = is.peek();
        if(isdigit(c)) {
            tmp.push_back(c);
            is >> c;
        } else if(c == '.') {
            if(has_dot == false) {
                tmp.push_back(c);
                is >> c;
                has_dot = true;
            } else {
                good = false;
                error_solve();
                break;
            }
        } else if(isalpha(c)){
            good = false;
            error_solve();
        } else {
            break;
        }
    }
    out = std::move(tmp);
    return good;
}

bool read_id(std::istream &is, std::string &out) {
    std::string tmp;
    while(is.good()) {
        char c = is.peek();
        if(isalnum(c)) {
            tmp.push_back(c);
            is >> c;
        } else {
            break;
        }
    }
    out = std::move(tmp);
    return true;
}


void token_output(Token token, int row, int col) {
    std::string st;
    switch (token.type)
    {
    case TokenType::KEYWORD:
        st = "KeyWord";
        break;
    case TokenType::IDENTIFIER:
        st = "Identifier";
        break;
    
    case TokenType::CONSTANT:
        st = "Constant";
        break;
    
    case TokenType::SEPARATOR:
        st = "Separator";
        break;

    case TokenType::ALG_OP:
        st = "Algrithm operator";
        break;

    case TokenType::CMP_OP:
        st = "Comparsion operator";
        break;
    }

    std::cout 
        << token.st<< "\t\t"
        << '(' << static_cast<int>(token.type) << ", "
        << token.st<< ')' << "\t\t"
        << st << "\t\t"
        << '(' << row << ", " << col << ')'
        << std::endl;
}

void error_output(std::string st, int row, int col) {
    std::cout << st << "\t\tError\t\tError\t\t"
        << '(' << row << ", " << col << ')'
        << std::endl;
}


int main(void) {
    std::vector<std::string> key;
    std::vector<std::string> id;

    std::vector<char> sep;
    std::vector<std::string> alg_op;
    std::vector<std::string> cmp_op;

    std::vector<std::string> num;
    std::vector<Token> tokens;

    input_stub(key, "Please input keys:\n");
    input_stub(sep, "Please input separators:\n");
    input_stub(alg_op, "Please input algorithm operators:\n");
    input_stub(cmp_op, "Please input comprasion operators:\n");

    std::string fn;
    std::cout << "Please input the source file name:\n";
    std::cin >> fn;
    std::ifstream sf;
    sf.open(fn);

    size_t row = 0, col = 0;
    char c;

    sf.unsetf(std::ios_base::skipws);
    while(sf.good()) {
        c = sf.peek();

        if(c == EOF) {
            break;
        }

        if(c == '\n') {
            ++row;
            col = 0;
            sf >> c;
        }else if(isblank(c)) {
            sf >> c;
        } else if(isdigit(c)) {
            // first char is digits, reading constants
            std::string tmp;
            bool ret = read_constant(sf, tmp);
            if(ret) {
                auto p = is_in(num, tmp);
                if(p == -1) {
                    p = num.size();
                    num.push_back(tmp);
                }
                auto token = Token{TokenType::CONSTANT, tmp, p};
                token_output(token, row, col++);
                tokens.push_back(token);
            } else {
                error_output(tmp, row, col++);
            }

        } else if(isalpha(c)) {
            // first char is alpha, reading identifier
            std::string tmp;
            bool ret = read_id(sf, tmp);
            if(ret) {
                auto p = is_in(key, tmp);
                TokenType tt = TokenType::KEYWORD;
                if(p == -1) {
                    tt = TokenType::IDENTIFIER;
                    p = id.size();
                    id.push_back(tmp);
                }
                auto token = Token{tt, tmp, p};
                token_output(token, row, col++);
                tokens.push_back(token);
            } else {
                error_output(tmp, row, col++);
            }
        } else {
            // reading all symbols and try matching
            std::string tmp;
            while(sf.good()) {
                c = sf.peek();
                if(isalnum(c) || isblank(c) || c == '\n') {
                    if(auto t = is_in(alg_op, tmp); t!= -1) {
                        tokens.emplace_back(TokenType::ALG_OP, tmp, t);
                        token_output(tokens.back(), row, col++);
                    } else if(auto t = is_in(cmp_op, tmp); t!= -1) {
                        tokens.emplace_back(TokenType::CMP_OP, tmp, t);
                        token_output(tokens.back(), row, col++);
                    } else {
                        error_output(tmp, row, col++);
                    }
                    break;
                } else {
                    if(auto p = is_in(sep, c); p != -1) {
                        if(tmp.size()) {
                            if(auto t = is_in(alg_op, tmp); t!= -1) {
                                tokens.emplace_back(TokenType::ALG_OP, tmp, t);
                                token_output(tokens.back(), row, col++);
                            } else if(auto t = is_in(cmp_op, tmp); t!= -1) {
                                tokens.emplace_back(TokenType::CMP_OP, tmp, t);
                                token_output(tokens.back(), row, col++);
                            } else {
                                error_output(tmp, row, col++);
                            }
                        }
                        tokens.emplace_back(TokenType::SEPARATOR, std::string{c}, p);
                        token_output(tokens.back(), row, col++);
                        sf >> c;
                        break;
                    } else {
                        tmp.push_back(c);
                        sf >> c;
                    }
                }
            }

       }
    }

    return 0;
    
}