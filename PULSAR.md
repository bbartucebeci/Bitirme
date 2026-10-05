# **PULSAR** 

Çalışmayı birbirini takip eden **üç ana bölüm** altında ele almayı ve her bölümün çıktısını bir sonraki bölümün girdisi olacak şekilde ilerlemeyi öneriyorum. Genel olarak hedefimiz; elektronik destek sistemleri (ESM/ELINT) tarafından elde edilen **Pulse Description Word (PDW)** bilgilerinden yararlanarak radar darbelerinin gelecekteki davranışını tahmin etmek, bu amaçla zaman serisi foundation modellerini değerlendirmek ve son aşamada uygun bir modelin FPGA üzerinde gerçek zamanlı çalıştırılmasını sağlamaktır. 

## **1. Bölüm – Literatür Taraması ve Problem Tanımının Oluşturulması** 

İlk aşamada radar sinyallerinin karakteristikleri, ESM sistemlerinin ölçüm kabiliyetleri ve mevcut radar darbe tahmin/deinterleaving yöntemleri incelenecektir. 

## **1.1. Radar Sinyal Türleri ve Parametreleri** 

Öncelikle farklı radar sinyal türleri ve bunların PDW üzerinde oluşturduğu karakteristikler araştırılacaktır. 

Bu kapsamda; 

- Radar sinyal modülasyon türleri, 

- CW, pulsed radar ve burst yapıları, 

- LFM/Chirp, phase-coded ve diğer pulse modulation teknikleri, 

- Frequency-agile ve frequency-hopping radarlar, 

- PRI çeşitleri: 

   - Stable PRI, 

   - Jittered PRI, 

   - Staggered PRI, 

   - Dwell-and-switch, 

   - Sliding PRI, 

   - Complex/Patterned PRI, 

- Pulse width ve amplitude davranışları, 

- Frequency ve angle-of-arrival değişimleri 

incelenecektir. 

Buradaki temel amaç, farklı radar davranışlarının PDW zaman serilerine nasıl yansıdığını ortaya koymaktır. 

## **1.2. ESM Sistemlerinin Doğrudan Ölçtüğü PDW Parametreleri** 

Elektronik destek sistemlerinin radar sinyalini algıladıktan sonra doğrudan ölçebildiği parametreler incelenecektir. 

Özellikle aşağıdaki PDW parametreleri ele alınacaktır: 

- **Time of Arrival (TOA)** 

- **Frequency** 

- **Pulse Width (PW)** 

- **Amplitude / Power** 

- **Angle of Arrival (AOA/DOA)** 

- Gerekli olması durumunda: 

   - Pulse modulation bilgisi, 

- Bandwidth, 

- Phase, 

- Frequency slope vb. 

Bunun yanında, doğrudan ölçülen parametreler ile sistem tarafından hesaplanan/türetilen parametrelerin ayrımı yapılacaktır. 

Örneğin: 

## **Doğrudan ölçülen:** 

TOA, Frequency, PW, Amplitude, AOA 

## **Türetilen:** 

PRI = TOA(n) - TOA(n-1) 

gibi parametreler değerlendirilecektir. 

## **1.3. PRI Hesaplama ve Deinterleaving** 

Birden fazla radarın aynı anda algılanması durumunda ESM sisteminin farklı yayıcıların darbelerini birbirinden ayırması önemli bir problem olarak ele alınacaktır. 

Bu kapsamda; 

- TOA tabanlı PRI estimation, 

- PRI histogram yöntemleri, 

- Sequential difference histogram, 

- PRI transform, 

- Clustering tabanlı yöntemler, 

- Statistical deinterleaving, 

- Rule-based deinterleaving, 

- Adaptive deinterleaving, 

- Machine-learning/deep-learning tabanlı yöntemler 

araştırılacaktır. 

Özellikle farklı radarların darbelerinin birbirine karıştığı **interleaved PDW** senaryolarında hangi parametrelerin kullanılarak pulse association yapıldığı incelenecektir. 

Buradaki temel soru: 

ESM'nin elde ettiği PDW'lerden hangi yöntemlerle aynı radara ait darbeler belirlenebilir ve bu darbeler kullanılarak radarın PRI davranışı nasıl çıkarılabilir? 

olacaktır. 

## **1.4. Radar Darbelerinin Geleceğe Yönelik Tahmini** 

Bir sonraki aşamada, geçmiş PDW bilgilerini kullanarak gelecekte oluşması beklenen radar darbelerinin tahmini araştırılacaktır. 

Örneğin geçmişte; 

TOA(n), TOA(n-1), ... 

ve 

PRI(n), PRI(n-1), ... 

bilgileri mevcut olduğunda; 

- Bir sonraki **TOA** , 

- Bir sonraki **PRI** , 

- Bir sonraki **Frequency** , 

- Gerekli olması halinde **PW, Amplitude ve AOA** 

değerlerinin tahmin edilmesi incelenecektir. 

Özellikle şu radar davranışları için prediction yöntemleri araştırılacaktır: 

- Stable PRI 

- Jitter PRI 

- Stagger PRI 

- Sliding PRI 

- Frequency agility 

- Frequency hopping 

- Birden fazla parametrenin birlikte değiştiği karmaşık radar davranışları 

Burada klasik yöntemler ile makine öğrenmesi/deep learning tabanlı yöntemlerin karşılaştırılması planlanmaktadır. 

## **1.5. Sentetik PDW Veri Setinin Oluşturulması** 

Literatür araştırmasının sonucunda elde edilen radar davranış modelleri kullanılarak sonraki aşamalarda kullanılmak üzere **sentetik PDW veri setleri** oluşturulacaktır. 

Sentetik veri üretiminde; 

- Farklı radar tipleri, 

- Farklı PRI davranışları, 

- Frequency agility, 

- PW değişimleri, 

- Amplitude değişimleri, 

- AOA değişimleri, 

- Measurement error, 

- TOA jitter, 

- Frequency measurement error, 

- Missing pulse, 

- False pulse, 

- Pulse-on-pulse, 

- Birden fazla radarın interleaving durumu 

gibi gerçek ESM sistemlerinde karşılaşılabilecek durumların modellenmesi hedeflenmektedir. 

Bu veri seti, ikinci bölümde foundation modellerinin değerlendirilmesi ve fine-tuning aşamalarında kullanılacaktır. 

## **2. Bölüm – Time-Series Foundation Models** 

İkinci bölümde, birinci bölümde oluşturulan PDW veri setlerinin **time-series foundation models** ile işlenip işlenemeyeceği araştırılacaktır. 

## **2.1. TimesFM Modellerinin PDW Tahmininde Kullanılması** 

Öncelikle açık kaynak olarak erişilebilen: 

- **TimesFM 2.5** 

- **TimesFM 3.0** 

modellerinin PDW tahmini için uygunluğu araştırılacaktır. 

Buradaki temel soru: 

ESM tarafından ölçülen PDW parametreleri ve bunlardan hesaplanan PRI bilgileri, time-series foundation model tarafından anlamlı bir zaman serisi olarak kullanılabilir mi? 

Örneğin model girdisi olarak; 

TOA(t), PRI(t), Frequency(t), PW(t), Amplitude(t), AOA(t) 

gibi parametrelerin kullanılması ve hedef olarak; 

TOA(t+1), PRI(t+1), Frequency(t+1) 

değerlerinin tahmin edilmesi değerlendirilecektir. 

Burada özellikle **univariate, multivariate ve covariate** kullanım şekillerinin PDW problemi açısından karşılaştırılması gerekmektedir. 

## **2.2. Farklı Foundation Modellerinin Araştırılması** 

TimesFM dışında açık kaynak olarak erişilebilen diğer time-series foundation modelleri de araştırılacaktır. 

Modeller; 

- Model boyutu, 

- Context length, 

- Multivariate destek, 

- Covariate desteği, 

- Fine-tuning kabiliyeti, 

- LoRA/PEFT desteği, 

- Inference latency, 

- GPU/CPU kaynak ihtiyacı, 

- FPGA'ye aktarılabilirlik 

gibi kriterler açısından teknik olarak incelenecektir. 

Amaç yalnızca en yüksek tahmin doğruluğuna sahip modeli bulmak değil, aynı zamanda üçüncü bölümdeki **gerçek zamanlı FPGA uygulamasına aktarılabilecek bir yaklaşım** belirlemektir. 

## **2.3. PDW Verileri ile Fine-Tuning** 

Foundation modelin genel zaman serisi bilgisinden yararlanarak, radar/ESM özelindeki PDW davranışlarına adapte edilmesi araştırılacaktır. 

Örneğin: 

## **TimesFM 3.0 + PDW Dataset + LoRA/PEFT** 

yaklaşımı değerlendirilebilir. 

Fine-tuning sırasında; 

- Radar tipi, 

- PRI davranışı, 

- Frequency davranışı, 

- Measurement noise, 

- Missing/false pulse, 

- Interleaving 

gibi ESM problemine özgü özelliklerin modele kazandırılması hedeflenecektir. 

## **2.4. Performans Değerlendirmesi** 

Modellerin performansı yalnızca klasik time-series metrikleriyle değil, ESM/radar açısından anlamlı kriterlerle de değerlendirilecektir. 

Örneğin: 

- TOA prediction error, 

- PRI prediction error, 

- Frequency prediction error, 

- PW prediction error, 

- Prediction error distribution, 

- Prediction horizon, 

- Radar pulse association accuracy, 

- Computational complexity, 

- Inference latency 

değerlendirilebilir. 

Ayrıca farklı radar davranışlarında model performansının nasıl değiştiği incelenecektir. 

## **3. Bölüm – FPGA Üzerinde Gerçek Zamanlı Prediction** 

Son bölümün amacı, ikinci bölümde elde edilen modelin veya modelden türetilen daha küçük bir modelin **FPGA üzerinde gerçek zamanlı olarak çalıştırılmasıdır.** 

## **3.1. Foundation Modelin FPGA'ye Doğrudan Aktarılması** 

Öncelikle TimesFM veya seçilen foundation modelin doğrudan FPGA üzerinde çalıştırılabilirliği araştırılacaktır. 

Bu kapsamda; 

- Model parametre sayısı, 

- Model memory footprint, 

- DSP kullanım miktarı, 

- BRAM/URAM ihtiyacı, 

- MAC operasyon sayısı, 

- Quantization ihtiyacı, 

- Inference latency, 

- Throughput 

analiz edilecektir. 

Model boyutu ve hesaplama karmaşıklığı nedeniyle foundation modelin doğrudan FPGA üzerinde çalıştırılması mümkün değilse, bu durum üçüncü bölümün tasarım kısıtı olarak değerlendirilecektir. 

## **3.2. Teacher–Student Model Yaklaşımı** 

Foundation modelin FPGA'ye doğrudan aktarılması mümkün değilse, **Teacher–Student Knowledge Distillation** yaklaşımı uygulanacaktır. 

Burada: 

## **Teacher:** 

Large Time-Series Foundation Model 

## **Student:** 

Small FPGA-Friendly Time-Series Model 

şeklinde bir yapı oluşturulacaktır. 

Teacher model, sentetik ve/veya gerçek PDW verileri üzerinde eğitilerek yüksek kaliteli prediction çıktıları üretecek; Student model ise Teacher'ın tahmin davranışını öğrenmeye çalışacaktır. 

Bu şekilde foundation modelin öğrendiği zaman serisi ilişkilerinin daha küçük bir modele aktarılması hedeflenmektedir. 

## **3.3. FPGA-Friendly Student Model** 

Student model tasarımında aşağıdaki kriterler dikkate alınacaktır: 

- Düşük parametre sayısı, 

- Düşük DSP kullanımı, 

- Düşük BRAM/URAM kullanımı, 

- Fixed-point implementation, 

- Pipeline edilebilir mimari, 

- Paralel işlem, 

- Deterministic latency, 

- Yüksek throughput. 

Gerekli olması durumunda; 

- Quantization, 

- Pruning, 

- Knowledge distillation, 

- Low-rank approximation 

gibi yöntemler de değerlendirilecektir. 

## **3.4. FPGA Implementation** 

Student modelin FPGA üzerinde gerçekleştirilmesi planlanmaktadır. 

Hedef FPGA platformuna bağlı olarak; 

- VHDL/Verilog/SystemVerilog implementation, 

- HLS implementation, 

- Fixed-point arithmetic, 

- Pipeline architecture, 

- Parallel MAC architecture, 

- Memory optimization 

konuları ele alınacaktır. 

Gerçek zamanlı sistem açısından özellikle: 

## **Input PDW → Preprocessing → Prediction Model → Next TOA/PRI/Frequency → Output** 

akışının deterministik bir latency ile gerçekleştirilmesi hedeflenecektir. 

## **3.5. Software–FPGA Karşılaştırması** 

Son aşamada aynı PDW veri setleri kullanılarak; 

## **Foundation Model** 

vs. 

## **Fine-Tuned Foundation Model** 

vs. 

## **Student Model** 

vs. 

## **FPGA Student Model** 

karşılaştırması yapılacaktır. 

Karşılaştırmada; 

- Prediction accuracy, 

- TOA error, 

- PRI error, 

- Frequency error, 

- Model size, 

- Memory usage, 

- Computational complexity, 

- Inference latency, 

- Throughput, 

- FPGA resource utilization 

gibi kriterler raporlanacaktır. 

Böylece yalnızca tahmin doğruluğu değil, **doğruluk–karmaşıklık–gecikme–kaynak kullanımı** arasındaki trade-off da ortaya konulmuş olacaktır. 

## **Genel Proje Akışı** 

Çalışmanın genel akışını aşağıdaki şekilde özetleyebiliriz: 

## **Literature Review** 

↓ 

## **Radar / ESM / PDW Analysis** ↓ 

## **PRI Estimation & Deinterleaving** 

↓ 

**Synthetic PDW Generation** ↓ 

**Time-Series Foundation Models** 

↓ 

**TimesFM 2.5 / 3.0 ve diğer modellerin değerlendirilmesi** ↓ 

## **PDW-specific Fine-Tuning / LoRA** 

↓ 

## **Radar Pulse Prediction** 

↓ **Teacher–Student Knowledge Distillation** 

↓ 

**FPGA-Friendly Student Model** ↓ 

## **FPGA Implementation** 

## ↓ 

## **Real-Time Prediction & Performance Comparison** 

Bu yapıyla çalışmanın sonunda, **ESM tarafından elde edilen PDW bilgilerinden gelecekteki radar darbelerinin tahmin edilmesi için foundation model tabanlı bir yaklaşımın uygulanabilirliği** ve bunun **FPGA üzerinde gerçek zamanlı çalıştırılabilirliği** birlikte değerlendirilmiş olacaktır. 

İlk aşamada literatür taramasının kapsamını netleştirip, özellikle **PDW → PRI/Deinterleaving → Pulse Prediction** zincirine odaklanarak bir teknik doküman oluşturmamızın uygun olacağını düşünüyorum. 

