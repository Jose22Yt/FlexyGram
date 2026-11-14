package tw.nekomimi.nekogram.utils

import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withTimeoutOrNull
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.Call
import okhttp3.Callback
import okhttp3.Response
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.telegram.messenger.FileLog
import org.telegram.messenger.UserConfig
import org.telegram.tgnet.ConnectionsManager
import org.xbill.DNS.AAAARecord
import org.xbill.DNS.ARecord
import org.xbill.DNS.Cache
import org.xbill.DNS.DClass
import org.xbill.DNS.Message
import org.xbill.DNS.Name
import org.xbill.DNS.Rcode
import org.xbill.DNS.Record
import org.xbill.DNS.SetResponse
import org.xbill.DNS.TXTRecord
import org.xbill.DNS.Type
import tw.nekomimi.nekogram.NekoConfig
import java.io.IOException
import java.net.Inet4Address
import java.net.Inet6Address
import java.net.InetAddress
import java.net.NetworkInterface
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlin.coroutines.resume

object DnsFactory {

    private const val USE_IPV4_ONLY: Byte = 0
    private const val USE_IPV6_ONLY: Byte = 1
    private const val USE_IPV4_IPV6_RANDOM: Byte = 2

    private val httpClient = OkHttpClient.Builder().callTimeout(10, TimeUnit.SECONDS).build()

    @Volatile
    private var ipStrategy: Byte = -1
    private var lastForceIPv6 = false
    private var lastUseIPv6 = false
    @Volatile private var networkGeneration = 0L

    @Volatile
    private var hasIPv4: Boolean = false

    @Volatile
    private var hasStrangeIPv4: Boolean = false

    @Volatile
    private var hasIPv6: Boolean = false


    private val cache = Cache()

    private val DEFAULT_DOH_PROVIDERS = arrayOf(
        "https://1.1.1.1/dns-query",
        "https://1.0.0.1/dns-query",
        "https://8.8.8.8/dns-query",
        "https://8.8.4.4/dns-query",
        "https://[2606:4700:4700::1001]/dns-query", // Cloudflare IPv6
        "https://[2001:4860:4860::8844]/dns-query", // Google IPv6
    )

    private fun providers(): Array<String> {
        if (NekoConfig.dnsType.Int() != NekoConfig.DNS_TYPE_CUSTOM_DOH) {
            return DEFAULT_DOH_PROVIDERS
        }

        val validCustomProviders = NekoConfig.customDoH.String()
            .split(",")
            .map { it.trim() }
            .filter { url ->
                url.toHttpUrlOrNull()?.isHttps == true
            }

        return if (validCustomProviders.isNotEmpty()) {
            validCustomProviders.toTypedArray()
        } else {
            DEFAULT_DOH_PROVIDERS
        }
    }

    @JvmStatic
    @JvmOverloads
    fun lookup(domain: String, fallback: Boolean = false): List<InetAddress> =
        lookupInternal(domain, fallback, 8)

    private fun lookupInternal(domain: String, fallback: Boolean, remaining: Int): List<InetAddress> {
        if (remaining <= 0) return emptyList()
        if (NekoConfig.dnsType.Int() != NekoConfig.DNS_TYPE_SYSTEM) {
            FileLog.d("Lookup for '$domain' requested (fallback=$fallback)")

            val type = getDnsQueryType(fallback)
            val dc = DClass.IN
            val name = Name(domain, Name.root)

            val sr = cache.lookupRecords(name, type, dc)
            val cachedResult = srToAddresses(sr, domain, isCache = true, fallback = fallback, remaining = remaining)
            if (cachedResult != null) {
                FileLog.d("Cache hit for '$domain'. Returning cached result: ${cachedResult.map { it.hostAddress }}")
                return cachedResult
            }
            FileLog.d("Cache miss for '$domain' (type: ${Type.string(type)}). Performing DoH query.")

            val message = Message.newQuery(Record.newRecord(name, type, dc)).toWire()

            val response = runBlocking {
                withTimeoutOrNull(5000L) {
                    queryProviders(message) { result ->
                        val answer = cache.addMessage(result)
                        val hasAddresses = answer?.isSuccessful == true && answer.answers().any { rrset ->
                            rrset.rrs(true).any { it is ARecord || it is AAAARecord }
                        }
                        val canTryOtherFamily = answer?.isNXRRSET == true && hasIPv4 && hasIPv6 && !fallback
                        if (hasAddresses || answer?.isCNAME == true || canTryOtherFamily) answer else null
                    }
                }
            }
            // Follow aliases outside OkHttp callbacks, after losing calls were cancelled.
            val ret = srToAddresses(response, domain, isCache = false, fallback = fallback, remaining = remaining)

            if (ret != null) {
                FileLog.d("DoH lookup for '$domain' succeeded.")
                return ret
            } else {
                FileLog.w("All DoH providers failed or timed out for '$domain'.")
            }
        }

        FileLog.d("Using system DNS for '$domain'.")
        try {
            val addresses = InetAddress.getAllByName(domain).toList()
            FileLog.d("System DNS resolved '$domain' to: ${addresses.map { it.hostAddress }}")
            return addresses
        } catch (e: Exception) {
            FileLog.e("System DNS lookup for '$domain' failed: ${e.message ?: e.javaClass.simpleName}")
        }

        FileLog.e("All DNS resolution methods failed for '$domain'.")
        return listOf()
    }

    @JvmStatic
    fun getTxtRecords(domain: String): List<String> {
        FileLog.d("TXT lookup for '$domain' requested")

        val type = Type.TXT
        val dc = DClass.IN
        val name = Name(domain, Name.root)

        fun srToTxtRecords(sr: SetResponse?): List<String>? {
            if (sr != null && sr.isSuccessful) {
                return sr.answers()
                    .flatMap { it.rrs(true) }
                    .filterIsInstance<TXTRecord>()
                    .flatMap { it.strings }
            }
            return null
        }

        val sr = cache.lookupRecords(name, type, dc)
        val cachedResult = srToTxtRecords(sr)
        if (cachedResult != null) {
            FileLog.d("Cache hit for '$domain' (TXT). Returning cached result: $cachedResult")
            return cachedResult
        }
        FileLog.d("Cache miss for '$domain' (TXT). Performing DoH query.")

        val message = Message.newQuery(Record.newRecord(name, type, dc)).toWire()

        val ret = runBlocking {
            withTimeoutOrNull(5000L) {
                queryProviders(message) { result -> srToTxtRecords(cache.addMessage(result)) }
            }
        }

        if (ret != null) {
            FileLog.d("DoH TXT lookup for '$domain' succeeded.")
            return ret
        } else {
            FileLog.w("All DoH providers failed or timed out for '$domain' (TXT).")
            return listOf()
        }
    }

    /** Async calls have no blocking coroutine children: the first useful answer wins.
     * Cancel every losing call both on success and on timeout, and always close bodies.
     */
    private suspend fun <T : Any> queryProviders(message: ByteArray, decode: (Message) -> T?): T? =
        suspendCancellableCoroutine { continuation ->
            val generation = networkGeneration
            val calls = providers().map { provider ->
                httpClient.newCall(Request.Builder().url(provider)
                    .header("accept", "application/dns-message")
                    .post(message.toRequestBody("application/dns-message".toMediaTypeOrNull()))
                    .build())
            }
            val completed = AtomicBoolean(false)
            val pending = AtomicInteger(calls.size)
            continuation.invokeOnCancellation {
                completed.set(true)
                calls.forEach { it.cancel() }
            }
            fun failed() {
                if (pending.decrementAndGet() == 0 && completed.compareAndSet(false, true)) {
                    continuation.resume(null)
                }
            }
            for (call in calls) {
                if (completed.get()) break
                call.enqueue(object : Callback {
                    override fun onFailure(call: Call, error: IOException) = failed()
                    override fun onResponse(call: Call, response: Response) {
                        try {
                            response.use {
                                if (completed.get() || !it.isSuccessful) return@use
                                val result = Message(it.body.bytes())
                                val rcode = result.header.rcode
                                if (rcode != Rcode.NOERROR && rcode != Rcode.NXDOMAIN && rcode != Rcode.NXRRSET) return@use
                                val value = synchronized(this@DnsFactory) {
                                    if (generation == networkGeneration && !completed.get()) {
                                        decode(result)?.takeIf { completed.compareAndSet(false, true) }
                                    } else null
                                }
                                if (value != null) {
                                    // Cancel before resuming so an immediate new lookup cannot
                                    // compete with obsolete requests in OkHttp's dispatcher.
                                    calls.forEach { other -> if (other !== call) other.cancel() }
                                    continuation.resume(value)
                                }
                            }
                        } catch (error: Exception) {
                            if (!completed.get()) FileLog.e(error)
                        } finally {
                            failed()
                        }
                    }
                })
                // Cancellation can race enqueue after the preflight check.
                if (completed.get()) call.cancel()
            }
        }

    /** Discard network-specific family selection and cached answers on connectivity changes. */
    @JvmStatic
    fun invalidateNetworkState() {
        synchronized(this) {
            networkGeneration++
            ipStrategy = -1
            cache.clearCache()
        }
    }

    private fun srToAddresses(
        sr: SetResponse?, domain: String, isCache: Boolean, fallback: Boolean, remaining: Int
    ): List<InetAddress>? {
        if (sr == null) return null

        val source = if (isCache) "Cache" else "DoH Response"

        if (sr.isSuccessful) {
            val records = sr.answers().flatMap { it.rrs(true) }
            val addresses = records.mapNotNull {
                (it as? ARecord)?.address ?: (it as? AAAARecord)?.address
            }
            if (addresses.isNotEmpty()) {
                FileLog.d("[$source] Successfully found ${addresses.size} records for '$domain'.")
                return addresses
            }
        }

        if (sr.isCNAME) {
            val cname = sr.cname.target.toString(true)
            FileLog.d("[$source] '$domain' is a CNAME pointing to '$cname'. Following redirection.")
            return lookupInternal(cname, false, remaining - 1)
        }

        val noFallbackAvailable = !hasIPv4 || !hasIPv6
        if (sr.isNXRRSET && !noFallbackAvailable && !fallback) {
            FileLog.d("[$source] for '$domain' resulted in NXRRSET. Trying fallback IP version.")
            return lookupInternal(domain, true, remaining - 1)
        }

        return null
    }

    @Synchronized
    private fun getIpStrategy(): Byte {
        val forceIPv6 = ConnectionsManager.getInstance(UserConfig.selectedAccount).forceTryIPv6
        val useIPv6 = NekoConfig.useIPv6.Bool()
        if (ipStrategy.toInt() != -1 && forceIPv6 == lastForceIPv6 && useIPv6 == lastUseIPv6) return ipStrategy
        lastForceIPv6 = forceIPv6
        lastUseIPv6 = useIPv6

        hasIPv4 = false
        hasStrangeIPv4 = false
        hasIPv6 = false

        FileLog.d("Determining IP strategy...")

        try {
            val networkInterfaces = NetworkInterface.getNetworkInterfaces()
            while (networkInterfaces.hasMoreElements()) {
                val networkInterface = networkInterfaces.nextElement()
                if (!networkInterface.isUp || networkInterface.isLoopback) {
                    continue
                }
                for (address in networkInterface.interfaceAddresses) {
                    val inetAddress = address.address
                    if (inetAddress.isLinkLocalAddress || inetAddress.isLoopbackAddress || inetAddress.isMulticastAddress) {
                        continue
                    }
                    when (inetAddress) {
                        is Inet6Address -> hasIPv6 = true
                        is Inet4Address -> {
                            if (inetAddress.hostAddress?.startsWith("192.0.0.") == false) {
                                hasIPv4 = true
                            } else {
                                hasStrangeIPv4 = true
                            }
                        }
                    }
                }
            }

            val determinedStrategy = when {
                hasIPv6 -> when {
                    !hasIPv4 -> USE_IPV6_ONLY
                    forceIPv6 -> USE_IPV6_ONLY
                    useIPv6 -> USE_IPV6_ONLY
                    hasStrangeIPv4 -> USE_IPV4_IPV6_RANDOM
                    else -> USE_IPV4_ONLY
                }

                else -> USE_IPV4_ONLY
            }
            ipStrategy = determinedStrategy

            val strategyName = when (determinedStrategy) {
                USE_IPV4_ONLY -> "IPv4 Only"
                USE_IPV6_ONLY -> "IPv6 Only"
                USE_IPV4_IPV6_RANDOM -> "IPv4 & IPv6 Random"
                else -> "Unknown"
            }
            FileLog.d("IP strategy set to: $strategyName. (hasIPv4=$hasIPv4, hasIPv6=$hasIPv6)")
        } catch (e: Throwable) {
            FileLog.e("Failed to determine IP strategy. Defaulting to IPv4 only.", e)
            ipStrategy = USE_IPV4_ONLY
        }

        return ipStrategy
    }

    private fun getDnsQueryType(fallback: Boolean): Int {
        val strategy = getIpStrategy()
        val noFallback = !hasIPv4 || !hasIPv6

        return if (noFallback) {
            if (hasIPv6 && !hasIPv4) Type.AAAA else Type.A
        } else {
            val preferred = when (strategy) {
                USE_IPV6_ONLY -> Type.AAAA
                USE_IPV4_ONLY -> Type.A
                USE_IPV4_IPV6_RANDOM -> if (NekoConfig.useIPv6.Bool()) Type.AAAA else Type.A
                else -> Type.A
            }
            if (fallback) {
                if (preferred == Type.A) Type.AAAA else Type.A
            } else preferred
        }
    }
}
