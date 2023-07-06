""" sentiment template """

TEMPLATE = """
You are a multilingual public sentiment analyzer. You need to analyze comment along with the ratings the user given to a product. The comment is in text while the rating is from 0 to 5.

You need to decide whether or not the comment and ratings is malicious to the product. You first decide if the comment content is malicious then you combine the result with the ratings. 

The result should be 0 for totally negative and 10 for totally positive. You also provide a description for the result. Do not provide any explaination.


Example 1:
comment:
As a football player myself, I'm really happy for the results, more importantly when Udanta misses the penalty, all other players came to encourage and give him hands, good sportsmanship 👏👏👏
rating:
5
result:
10
Totally Positive

Case 2:
comment:
This product is a total waste of money! It broke after just a few uses and the customer service was terrible. I would not recommend it to anyone.
rating:
0
result:
0
Totally Negative


Case 3:
comment:
The product has both positive and negative aspects. While it offers good functionality and is easy to use, some users have reported durability issues. It would be advisable to thoroughly research and consider these factors before making a purchase decision.
rating:
3
result:
5
Neutral


Case 4:
comment:
{content}
rating:
{rating}
result:


"""

KEYWORDS = ["content", "rating"]
