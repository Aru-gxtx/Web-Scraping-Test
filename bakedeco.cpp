#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <filesystem>
#include <algorithm> // For text cleaning
#include <curl/curl.h>
#include <libxml/HTMLparser.h>
#include <libxml/xpath.h>

using namespace std;
namespace fs = std::filesystem;

string clean_text(string str) {
    replace(str.begin(), str.end(), '\n', ' ');
    replace(str.begin(), str.end(), '\r', ' ');
    replace(str.begin(), str.end(), '\t', ' ');
    replace(str.begin(), str.end(), '\"', '\''); // Prevent CSV layout breaking
    
    // Remove extra spaces
    str.erase(unique(str.begin(), str.end(), [](char a, char b) { return a == ' ' && b == ' '; }), str.end());
    
    // Trim leading and trailing spaces
    if (!str.empty()) {
        str.erase(0, str.find_first_not_of(" "));
        size_t last = str.find_last_not_of(" ");
        if (last != string::npos) str.erase(last + 1);
    }
    return str.empty() ? "N/A" : str;
}

typedef size_t (*curl_write)(char *, size_t, size_t, std::string *);
size_t WriteCallback(char *contents, size_t size, size_t nmemb, std::string *data) {
    size_t new_size = size * nmemb;
    if (data == NULL) return 0;
    data->append(contents, new_size);
    return new_size;
}

string fetch_html(string url) {
    CURL *curl = curl_easy_init();
    string result;
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, static_cast<curl_write>(WriteCallback));
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &result);
        curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }
    return result;
}

string get_xpath_text(xmlXPathContextPtr context, const char* xpath_expr) {
    string result = "N/A";
    xmlXPathObjectPtr xpathObj = xmlXPathEvalExpression((const xmlChar*)xpath_expr, context);
    if (xpathObj && xpathObj->nodesetval && xpathObj->nodesetval->nodeNr > 0) {
        xmlNodePtr node = xpathObj->nodesetval->nodeTab[0];
        xmlChar* content = xmlNodeGetContent(node);
        if (content) {
            result = clean_text(string((char*)content));
            xmlFree(content);
        }
    }
    if (xpathObj) xmlXPathFreeObject(xpathObj);
    return result;
}

vector<string> get_product_links(string start_url) {
    cout << "Fetching product list from: " << start_url << " ...\n";
    string html = fetch_html(start_url);
    vector<string> links;

    htmlDocPtr doc = htmlReadMemory(html.data(), html.length(), NULL, NULL, HTML_PARSE_NOERROR | HTML_PARSE_NOWARNING);
    if (doc == NULL) return links;
    
    xmlXPathContextPtr context = xmlXPathNewContext(doc);
    xmlXPathObjectPtr result = xmlXPathEvalExpression((xmlChar *)"//div[contains(@class, 'prd_list_mid')]//a[@href]", context);
    
    if (result && result->nodesetval) {
        for (int i = 0; i < result->nodesetval->nodeNr; ++i) {
            xmlNodePtr node = result->nodesetval->nodeTab[i];
            xmlChar* href = xmlGetProp(node, (const xmlChar*)"href");
            if (href) {
                string link_str = (char*)href;
                if (link_str.find("detail.asp") != string::npos) {
                    links.push_back("https://www.bakedeco.com/" + link_str);
                }
                xmlFree(href);
            }
        }
    }
    
    xmlXPathFreeObject(result);
    xmlXPathFreeContext(context);
    xmlFreeDoc(doc);
    
    cout << "-> Found " << links.size() << " products.\n";
    return links;
}

int main() {
    string START_URL = "https://www.bakedeco.com/nav/brand.asp?pagestart=1&categoryID=0&price=0&manufacid=551&sortby=&clearance=0&va=1";
    curl_global_init(CURL_GLOBAL_ALL);

    vector<string> all_links = get_product_links(START_URL);

    if (!all_links.empty()) {
        string folder_name = "results";
        fs::create_directory(folder_name);
        string output_path = folder_name + "/Bakedeco_Silikomart_Final.csv";
        ofstream csv_file(output_path);
        
        // Write the Headers
        csv_file << "Item Description,Item No.,List Price\n"; 
        
        // Loop through the links and scrape the data!
        for(size_t i = 0; i < all_links.size(); i++) {
            cout << "[" << (i+1) << "/" << all_links.size() << "] Scraping: " << all_links[i] << "\n";
            string product_html = fetch_html(all_links[i]);

            htmlDocPtr doc = htmlReadMemory(product_html.data(), product_html.length(), NULL, NULL, HTML_PARSE_NOERROR | HTML_PARSE_NOWARNING);
            if (!doc) continue;
            xmlXPathContextPtr context = xmlXPathNewContext(doc);

            // Extract Raw Text
            string title = get_xpath_text(context, "//h1");
            string item_no_raw = get_xpath_text(context, "//div[contains(@class, 'item-number')]");
            string price_raw = get_xpath_text(context, "//div[contains(@class, 'price')]");

            // Format Item Number (Isolate the number between "Item #" and "|")
            string item_no = "N/A";
            size_t item_pos = item_no_raw.find("Item #");
            if (item_pos != string::npos) {
                item_no = item_no_raw.substr(item_pos + 6);
                size_t bar_pos = item_no.find("|");
                if (bar_pos != string::npos) item_no = item_no.substr(0, bar_pos);
                item_no = clean_text(item_no);
            }

            // Format Price (Remove "Our Price:")
            string price = "N/A";
            size_t price_pos = price_raw.find("Our Price:");
            if (price_pos != string::npos) {
                price = price_raw.substr(price_pos + 10);
                price = clean_text(price);
            } else if (price_raw != "N/A") {
                price = price_raw;
            }

            // Write to CSV (Wrapped in quotes to protect commas)
            csv_file << "\"" << title << "\",\"" << item_no << "\",\"" << price << "\"\n";

            xmlXPathFreeContext(context);
            xmlFreeDoc(doc);
        }
        
        csv_file.close();
        cout << "\nSuccess! Saved to " << output_path << "\n";
    }

    curl_global_cleanup();
    return 0;
}