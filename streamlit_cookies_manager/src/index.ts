import {RenderData, Streamlit} from "streamlit-component-lib"

const topWindow: Window = window.top || window
const topDocument = topWindow.document

let lastValue: string | null = null

interface AddCookieSpec {
    value: string
    expires_at: string
    path: string
}

interface DeleteCookieSpec {
    value: null
    path: string
}

type CookieSpec = AddCookieSpec | DeleteCookieSpec

function onRender(event: Event): void {
    const data = (event as CustomEvent<RenderData>).detail
    console.log('args', data.args)
    saveCookies(data.args["queue"])

    const newValue = topDocument.cookie
    if (lastValue !== newValue && !data.args.saveOnly) {
        Streamlit.setComponentValue(newValue)
        lastValue = newValue
    }
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)
Streamlit.setComponentReady()
Streamlit.setFrameHeight(0)


function saveCookies(queue: { [k in string]: CookieSpec }) {
    Object.keys(queue).forEach((name) => {
        const spec = queue[name]
        if (spec.value === null)
            topDocument.cookie = `${encodeURIComponent(name)}=; path=${encodeURIComponent(spec.path)}`
        else {
            const date = new Date(spec.expires_at)
            topDocument.cookie = (
                `${encodeURIComponent(name)}=${encodeURIComponent(spec.value)};` +
                ` expires=${date.toUTCString()};` +
                ` path=${encodeURIComponent(spec.path)};`
            )
            console.log(`${encodeURIComponent(name)}=${encodeURIComponent(spec.value)};` +
                ` expires=${date.toUTCString()};` +
                ` path=${encodeURIComponent(spec.path)};`)
        }
    })
}