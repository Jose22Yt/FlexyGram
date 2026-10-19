package tw.nekomimi.nekogram.translate.source

import tw.nekomimi.nekogram.translate.TranslationServicesPolicy
import android.text.TextUtils
import okhttp3.FormBody
import okhttp3.Request
import org.json.JSONException
import org.json.JSONObject
import org.telegram.messenger.LocaleController.getString
import org.telegram.messenger.R
import org.telegram.tgnet.TLRPC
import org.telegram.ui.Components.TranslateAlert2
import tw.nekomimi.nekogram.NekoConfig
import tw.nekomimi.nekogram.translate.HTMLKeeper
import tw.nekomimi.nekogram.translate.Translator
import tw.nekomimi.nekogram.utils.HttpClient
import java.io.IOException

object GoogleCloudTranslator : Translator {

    private val httpClient by lazy { HttpClient.instance }

    override suspend fun doTranslate(
        from: String, to: String, query: String, entities: ArrayList<TLRPC.MessageEntity>
    ): TLRPC.TL_textWithEntities {
        TranslationServicesPolicy.requireRoute(TranslationServicesPolicy.Route.GOOGLE_CLOUD)

        if (to.lowercase() !in targetLanguages.map { it.lowercase() }) {
            throw UnsupportedOperationException(getString(R.string.TranslateApiUnsupported) + " " + to)
        }

        val apiKey = NekoConfig.googleCloudTranslateKey.String()
        if (TextUtils.isEmpty(apiKey)) error("Missing Cloud Translate Key")

        val originalText = TLRPC.TL_textWithEntities().apply {
            this.text = query
            this.entities = entities
        }

        val finalString = StringBuilder()

        val textToTranslate = if (entities.isNotEmpty()) HTMLKeeper.entitiesToHtml(
            query,
            entities,
            false
        ) else query

        val formBodyBuilder = FormBody.Builder()
            .add("q", textToTranslate)
            .add("target", to)
            .add("format", "text")
            .add("key", apiKey)

        if (from != "auto") {
            formBodyBuilder.add("source", from)
        }

        val requestBody = formBodyBuilder.build()
        val request = Request.Builder().url("https://translation.googleapis.com/language/translate/v2")
            .post(requestBody).build()

        val responseBodyString: String
        try {
            responseBodyString = httpClient.newCall(request).await().use { response ->
                val bodyString = response.body.string()
                if (!response.isSuccessful) {
                    error("TRANSLATION_HTTP_ERROR")
                }
                bodyString
            }
        } catch (e: kotlinx.coroutines.CancellationException) {
            throw e
        } catch (e: IOException) {
            throw TranslationServicesPolicy.safeFailure(e)
        } catch (e: Exception) {
            throw TranslationServicesPolicy.safeFailure(e)
        }

        try {
            var respObj = JSONObject(responseBodyString)

            if (respObj.isNull("data")) {
                error("TRANSLATION_INVALID_RESPONSE")
            }

            respObj = respObj.getJSONObject("data")
            val respArr = respObj.getJSONArray("translations")

            if (respArr.length() == 0) {
                error("Empty translation result")
            }

            val translatedText = respArr.getJSONObject(0).getString("translatedText")
            finalString.append(translatedText)
        } catch (e: JSONException) {
            throw TranslationServicesPolicy.safeFailure(e)
        }

        var finalText = TLRPC.TL_textWithEntities()
        if (entities.isNotEmpty()) {
            val resultPair = HTMLKeeper.htmlToEntities(finalString.toString(), entities, false)
            finalText.text = resultPair.first
            finalText.entities = resultPair.second
            finalText = TranslateAlert2.preprocess(originalText, finalText)
        } else {
            finalText.text = finalString.toString()
        }

        return finalText
    }

    private val targetLanguages = listOf(
            "sq", "ar", "am", "az", "ga", "et", "eu", "be", "bg", "is", "pl", "bs", "fa",
            "af", "da", "de", "ru", "fr", "tl", "fi", "fy", "km", "ka", "gu", "kk", "ht",
            "ko", "ha", "nl", "ky", "gl", "ca", "cs", "kn", "co", "hr", "ku", "la", "lv",
            "lo", "lt", "lb", "ro", "mg", "mt", "mr", "ml", "ms", "mk", "mi", "mn", "bn",
            "my", "hmn", "xh", "zu", "ne", "no", "pa", "pt", "ps", "ny", "ja", "sv", "sm",
            "sr", "st", "si", "eo", "sk", "sl", "sw", "gd", "ceb", "so", "tg", "te", "ta",
            "th", "tr", "cy", "ur", "uk", "uz", "es", "iw", "el", "haw", "sd", "hu", "sn",
            "hy", "ig", "it", "yi", "hi", "su", "id", "jw", "en", "yo", "vi", "zh-TW", "zh-CN", "zh")
}
