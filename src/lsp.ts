import { AceLanguageClient, type LanguageClientConfig, type ProviderOptions } from "ace-linters/build/ace-language-client";
export type LanguageProvider = ReturnType<typeof AceLanguageClient.for>;
if (window.pywebview && window.pywebview.api) {
    initLSP();
} else {
    window.addEventListener("pywebviewready", initLSP);
}
let languageProvider: LanguageProvider;
let resolveLanguageProviderList: ((value: LanguageProvider) => void)[] = [];
export function getLanguageProvider(): Promise<LanguageProvider> {
    return new Promise<LanguageProvider>((resolve) => {
        if (languageProvider) {
            resolve(languageProvider);
        } else {
            resolveLanguageProviderList.push(resolve);
        }
    });
}
async function initLSP() {
    const py = await window.pywebview.api;
    const langs = await py.get_langs();
    const options: ProviderOptions = {

        functionality: {
            hover: true,
            completion: {
                overwriteCompleters: true,
                lspCompleterOptions: { triggerCharacters: { add: ["."] } },
            },
            documentHighlights: true,
        },
    };
    let serverDataList: LanguageClientConfig[] = [];
    for (const lang of langs) {
        if (lang.lsp.length <= 0) continue;
        let mods_lst = lang.alias
        mods_lst.push(lang.id);
        serverDataList.push({
            module: () => import("ace-linters/build/language-client"),
            modes: mods_lst.join("|"),
            type: "socket" as "socket",
            socket: new WebSocket(
                `ws://127.0.0.1:${await py.get_port()}/lsp/${lang.id}`
            ),
        });
    }


    languageProvider = AceLanguageClient.for(serverDataList, options);
    for (const resolve of resolveLanguageProviderList) {
        resolve(languageProvider);
    }
    resolveLanguageProviderList = [];


}