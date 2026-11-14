"""Compile the production resolver and exercise callback races without public DNS/network."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_production_dns_returns_first_answer_closes_losers_and_bounds_aliases(tmp_path):
    maven = shutil.which('mvn')
    if not maven:
        pytest.skip('Maven and JDK required for Kotlin resolver regression')
    source = tmp_path / 'src/main/kotlin'
    source.mkdir(parents=True)
    resolver = (ROOT / 'TMessagesProj/src/main/java/tw/nekomimi/nekogram/utils/DnsFactory.kt').read_text()
    # Only relax finality of the private client to install a simulated HTTP transport.
    # All production resolver methods, cancellation and cache logic compile unchanged.
    (source / 'DnsFactory.kt').write_text(resolver.replace('private val httpClient =', 'private var httpClient ='))
    (source / 'Messenger.kt').write_text('''package org.telegram.messenger
object FileLog {fun d(s:String){};fun w(s:String){};fun e(s:String){};fun e(t:Throwable){};fun e(s:String,t:Throwable){}}
object UserConfig {var selectedAccount=0}
''')
    (source / 'Connections.kt').write_text('''package org.telegram.tgnet
class ConnectionsManager {var forceTryIPv6=false
companion object {val instance=ConnectionsManager();fun getInstance(account:Int)=instance}}
''')
    (source / 'Config.kt').write_text('''package tw.nekomimi.nekogram
class Entry(var number:Int=0,var text:String="",var flag:Boolean=false){fun Int()=number;fun String()=text;fun Bool()=flag}
object NekoConfig {const val DNS_TYPE_SYSTEM=1;const val DNS_TYPE_CUSTOM_DOH=2
val dnsType=Entry(2);val customDoH=Entry(text="https://fast.test/dns-query,https://slow.test/dns-query");val useIPv6=Entry()}
''')
    (source / 'Probe.kt').write_text('''import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import okio.Buffer
import org.xbill.DNS.*
import tw.nekomimi.nekogram.NekoConfig
import tw.nekomimi.nekogram.utils.DnsFactory
import java.net.InetAddress
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

fun main(){
 val clientField=DnsFactory::class.java.getDeclaredField("httpClient").apply{isAccessible=true}
 fun scenario(domain:String,txt:Boolean=false,alias:Boolean=false){
  val slowStarted=CountDownLatch(1);val release=CountDownLatch(1)
  @VolatilePlaceholder var unused=0
  val slowCall=java.util.concurrent.atomic.AtomicReference<Call>()
  val bodies=java.util.concurrent.atomic.AtomicInteger()
  val client=OkHttpClient.Builder().addInterceptor{chain->
   if(chain.request().url.host=="slow.test"){
    slowCall.set(chain.call());slowStarted.countDown();release.await(3,TimeUnit.SECONDS)
    throw java.io.IOException("slow simulated provider")
   }
   check(slowStarted.await(2,TimeUnit.SECONDS))
   val buffer=Buffer();chain.request().body!!.writeTo(buffer)
   val question=Message(buffer.readByteArray()).question
   val answer=Message().apply{
    header.setFlag(Flags.QR.toInt());addRecord(question,Section.QUESTION)
    val record=if(alias) CNAMERecord(question.name,DClass.IN,60,question.name)
     else if(txt) TXTRecord(question.name,DClass.IN,60,"configuration")
     else if(question.type==Type.AAAA) AAAARecord(question.name,DClass.IN,60,InetAddress.getByName("2001:db8::1"))
     else ARecord(question.name,DClass.IN,60,InetAddress.getByName("192.0.2.1"))
    addRecord(record,Section.ANSWER)
   }
   val bytes=answer.toWire()
   val body=object:ResponseBody(){
    val delegate=bytes.toResponseBody("application/dns-message".toMediaType())
    override fun contentType()=delegate.contentType()
    override fun contentLength()=delegate.contentLength()
    override fun source()=delegate.source()
    override fun close(){bodies.incrementAndGet();delegate.close()}
   }
   Response.Builder().request(chain.request()).protocol(Protocol.HTTP_1_1).code(200).message("OK").body(body).build()
  }.build()
  clientField.set(DnsFactory,client);DnsFactory.invalidateNetworkState()
  try{
   if(txt) check(DnsFactory.getTxtRecords(domain)==listOf("configuration"))
   else {val result=DnsFactory.lookup(domain);if(alias)check(result.isEmpty())else check(result.isNotEmpty())}
   // Return while the losing provider is still blocked, and actually cancel its call.
   check(release.count==1L);check(slowCall.get().isCanceled())
   for(i in 0..100){if(bodies.get()>0)break;Thread.sleep(2)}
   check(bodies.get()>0)
  }finally{release.countDown();client.dispatcher.executorService.shutdown();client.connectionPool.evictAll()}
 }
 scenario("answer.test")
 scenario("txt.test",txt=true)
 scenario("cycle.test",alias=true)
 // A timeout must return without waiting for a blocked transport callback.
 val release=CountDownLatch(1)
 val pending=java.util.concurrent.CopyOnWriteArrayList<Call>()
 val stalled=OkHttpClient.Builder().addInterceptor{chain->
  pending.add(chain.call());release.await(15,TimeUnit.SECONDS);throw java.io.IOException("stalled")
 }.build()
 clientField.set(DnsFactory,stalled);DnsFactory.invalidateNetworkState()
 try{
  val started=System.nanoTime();check(DnsFactory.getTxtRecords("timeout.test").isEmpty())
  check(TimeUnit.NANOSECONDS.toSeconds(System.nanoTime()-started)<8)
  check(release.count==1L&&pending.size==2&&pending.all{it.isCanceled()})
 }finally{release.countDown();stalled.dispatcher.executorService.shutdown();stalled.connectionPool.evictAll()}
 val strategy=DnsFactory::class.java.getDeclaredField("ipStrategy").apply{isAccessible=true}
 strategy.setByte(DnsFactory,7)
 val detect=DnsFactory::class.java.getDeclaredMethod("getIpStrategy").apply{isAccessible=true}
 org.telegram.tgnet.ConnectionsManager.instance.forceTryIPv6=true
 check((detect.invoke(DnsFactory) as Byte).toInt()!=7)
 val v4=DnsFactory::class.java.getDeclaredField("hasIPv4").apply{isAccessible=true}
 val v6=DnsFactory::class.java.getDeclaredField("hasIPv6").apply{isAccessible=true}
 v4.setBoolean(DnsFactory,true);v6.setBoolean(DnsFactory,true);strategy.setByte(DnsFactory,0)
 val queryType=DnsFactory::class.java.getDeclaredMethod("getDnsQueryType",Boolean::class.javaPrimitiveType).apply{isAccessible=true}
 check(queryType.invoke(DnsFactory,false)==Type.A);check(queryType.invoke(DnsFactory,true)==Type.AAAA)
 strategy.setByte(DnsFactory,1);check(queryType.invoke(DnsFactory,false)==Type.AAAA);check(queryType.invoke(DnsFactory,true)==Type.A)
 v4.setBoolean(DnsFactory,false);v6.setBoolean(DnsFactory,false);check(queryType.invoke(DnsFactory,false)==Type.A)
 DnsFactory.invalidateNetworkState();check(strategy.getByte(DnsFactory).toInt()==-1)
 println("DNS race, TXT, response closure, alias cycle and network invalidation passed")
}
'''.replace('  @VolatilePlaceholder var unused=0\n', ''))
    (tmp_path / 'pom.xml').write_text('''<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>
<groupId>app.flexygram.tests</groupId><artifactId>dns-regression</artifactId><version>1</version>
<dependencies>
<dependency><groupId>org.jetbrains.kotlin</groupId><artifactId>kotlin-stdlib</artifactId><version>2.3.20</version></dependency>
<dependency><groupId>org.jetbrains.kotlinx</groupId><artifactId>kotlinx-coroutines-core-jvm</artifactId><version>1.11.0</version></dependency>
<dependency><groupId>com.squareup.okhttp3</groupId><artifactId>okhttp-jvm</artifactId><version>5.5.0</version></dependency>
<dependency><groupId>dnsjava</groupId><artifactId>dnsjava</artifactId><version>3.6.5</version></dependency>
</dependencies><build><sourceDirectory>${project.basedir}/src/main/kotlin</sourceDirectory><plugins>
<plugin><groupId>org.jetbrains.kotlin</groupId><artifactId>kotlin-maven-plugin</artifactId><version>2.3.20</version><executions><execution><goals><goal>compile</goal></goals></execution></executions></plugin>
<plugin><groupId>org.codehaus.mojo</groupId><artifactId>exec-maven-plugin</artifactId><version>3.5.0</version><configuration><mainClass>ProbeKt</mainClass></configuration></plugin>
</plugins></build></project>''')
    command = [maven, '-q', '-B', '-Dkotlin.compiler.daemon=false', '-f', str(tmp_path / 'pom.xml')]
    if os.environ.get('FLEXY_MAVEN_SETTINGS'):
        command += ['-s', os.environ['FLEXY_MAVEN_SETTINGS']]
    result = subprocess.run(command + ['compile', 'exec:java'], capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'network invalidation passed' in result.stdout
